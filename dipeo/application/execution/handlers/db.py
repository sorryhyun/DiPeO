from __future__ import annotations

import glob
import json
import logging
import os
from typing import TYPE_CHECKING, Any, Optional

import yaml
from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.registry import DB_OPERATIONS_SERVICE
from dipeo.diagram_generated.generated_nodes import DBNode, NodeType
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.models.db_model import DbNodeData as DBNodeData
from dipeo.domain.ports.template import TemplateProcessorPort

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


@register_handler
class DBTypedNodeHandler(TypedNodeHandler[DBNode]):
    """
    Clean separation of concerns:
    1. validate() - Static/structural validation (compile-time checks)
    2. pre_execute() - Runtime validation and setup
    3. execute_with_envelopes() - Core execution logic with envelope inputs
    
    Now uses envelope-based communication for clean input/output interfaces.
    """
    

    def __init__(self, db_operations_service: Any | None = None, template_processor: TemplateProcessorPort | None = None) -> None:
        super().__init__()
        self.db_operations_service = db_operations_service
        self._template_processor = template_processor
        # Instance variables for passing data between methods
        self._current_db_service = None
        self._current_base_dir = None
        self._current_template_processor = None

    @property
    def node_class(self) -> type[DBNode]:
        return DBNode

    @property
    def node_type(self) -> str:
        return NodeType.DB.value

    @property
    def schema(self) -> type[BaseModel]:
        return DBNodeData

    @property
    def requires_services(self) -> list[str]:
        return ["db_operations_service"]

    @property
    def description(self) -> str:
        return "File-based DB node supporting read, write and append operations"
    
    async def pre_execute(self, request: ExecutionRequest[DBNode]) -> Optional[Envelope]:
        """Pre-execution setup: validate database service availability.
        
        Moves service resolution and validation out of execute_request
        for cleaner separation of concerns.
        """
        node = request.node
        
        # Resolve database operations service
        db_service = request.services.resolve(DB_OPERATIONS_SERVICE)
        
        if db_service is None:
            return EnvelopeFactory.error(
                "Database operations service not available",
                error_type="ValueError",
                produced_by=str(node.id)
            )
        
        # Validate operation type
        valid_operations = ["read", "write", "append"]
        if node.operation not in valid_operations:
            return EnvelopeFactory.error(
                f"Invalid operation: {node.operation}. Valid operations: {', '.join(valid_operations)}",
                error_type="ValueError",
                produced_by=str(node.id)
            )
        
        # Validate file paths are provided
        file_paths = node.file
        if not file_paths:
            return EnvelopeFactory.error(
                "No file paths specified for database operation",
                error_type="ValueError",
                produced_by=str(node.id)
            )
        
        # Store service and configuration in instance variables for execute_request
        self._current_db_service = db_service
        self._current_base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
        
        # Initialize template processor for path interpolation
        # Use injected processor or try to get from services
        from dipeo.application.registry.keys import TEMPLATE_PROCESSOR
        template_processor = self._template_processor
        if not template_processor:
            try:
                template_processor = request.services.resolve(TEMPLATE_PROCESSOR)
            except:
                # If not available in services, template processing will be skipped
                pass
        self._current_template_processor = template_processor
        
        # No early return - proceed to execute_request
        return None

    @staticmethod
    def _first_non_empty(inputs: dict[str, Any] | None) -> Any | None:
        if not inputs:
            return None
        for _k, v in inputs.items():
            if v is not None:
                return v
        return None

    @staticmethod
    def _expand_glob_patterns(file_paths: list[str], base_dir: str | None = None) -> list[str]:
        expanded_paths = []
        
        for path in file_paths:
            if any(char in path for char in ['*', '?', '[', ']']):
                if base_dir and not os.path.isabs(path):
                    pattern = os.path.join(base_dir, path)
                else:
                    pattern = path
                
                matches = glob.glob(pattern)
                if matches:
                    if base_dir and not os.path.isabs(path):
                        matches = [os.path.relpath(m, base_dir) for m in matches]
                    expanded_paths.extend(sorted(matches))
                else:
                    logger.warning(f"Glob pattern '{path}' matched no files")
            else:
                expanded_paths.append(path)
        
        return expanded_paths

    @staticmethod
    def _serialize_data(data: Any, format_type: str | None) -> str:
        if format_type == 'json':
            return json.dumps(data, indent=2)
        elif format_type == 'yaml':
            return yaml.dump(data, default_flow_style=False)
        elif format_type == 'text' or format_type is None:
            return str(data)
        else:
            logger.warning(f"Unknown format '{format_type}', using text format")
            return str(data)

    @staticmethod
    def _deserialize_data(content: str, format_type: str | None) -> Any:
        if not content:
            return content
            
        if format_type == 'json':
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON: {e}")
                return content
        elif format_type == 'yaml':
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse YAML: {e}")
                return content
        elif format_type == 'text' or format_type is None:
            return content
        else:
            logger.warning(f"Unknown format '{format_type}', returning as text")
            return content

    async def execute_with_envelopes(
        self, 
        request: ExecutionRequest[DBNode],
        inputs: dict[str, Envelope]
    ) -> Envelope:
        """Execute database operation with envelope inputs."""
        node = request.node
        context = request.context
        trace_id = request.execution_id or ""
        
        # Convert envelope inputs to legacy format
        legacy_inputs = {}
        for key, envelope in inputs.items():
            try:
                # Try to parse as JSON first
                legacy_inputs[key] = self.reader.as_json(envelope)
            except ValueError:
                # Fall back to text
                legacy_inputs[key] = self.reader.as_text(envelope)
        
        # Use pre-validated service and configuration from instance variables (set in pre_execute)
        db_service = self._current_db_service
        base_dir = self._current_base_dir
        template_processor = self._current_template_processor
        
        file_paths = node.file

        if isinstance(file_paths, str):
            file_paths = [file_paths]
        elif not file_paths:
            file_paths = []
        
        processed_paths = []
        for file_path in file_paths:
            if file_path and '{' in file_path and '}' in file_path:
                variables = {}
                if hasattr(context, 'get_variables'):
                    variables = context.get_variables()
                
                merged_variables = {**variables, **legacy_inputs}
                if template_processor:
                    file_path = template_processor.process_single_brace(file_path, merged_variables)

            processed_paths.append(file_path)
        
        format_type = getattr(node, 'format', None)
        
        if format_type and node.operation == "write":
            adjusted_paths = []
            for path in processed_paths:
                if format_type == 'yaml' and not path.endswith(('.yaml', '.yml')):
                    if '.' not in os.path.basename(path):
                        path = f"{path}.yaml"
                elif format_type == 'json' and not path.endswith('.json'):
                    if '.' not in os.path.basename(path):
                        path = f"{path}.json"
                adjusted_paths.append(path)
            processed_paths = adjusted_paths
        
        if getattr(node, 'glob', False):
            processed_paths = self._expand_glob_patterns(processed_paths, base_dir)

        if node.operation == "write":
            input_val = legacy_inputs.get('generated_code') or legacy_inputs.get('content') or legacy_inputs.get('value') or self._first_non_empty(legacy_inputs)
            if isinstance(input_val, dict):
                actual_content = input_val.get('generated_code') or input_val.get('content') or input_val.get('value')
                if actual_content is not None:
                    input_val = actual_content
            
            # Only serialize for YAML format or text format 
            # JSON serialization is handled by db_adapter
            if node.operation == "write" and format_type == 'yaml' and input_val is not None:
                if isinstance(input_val, (dict, list)):
                    input_val = self._serialize_data(input_val, 'yaml')
            elif node.operation == "write" and format_type == 'text' and input_val is not None:
                if not isinstance(input_val, str):
                    input_val = str(input_val)
        else:
            input_val = self._first_non_empty(legacy_inputs)

        try:
            if node.operation == "read" and len(processed_paths) > 1:
                results = {}
                serialize_json = getattr(node, 'serialize_json', False)
                for file_path in processed_paths:
                    try:
                        result = await db_service.execute_operation(
                            db_name=file_path,
                            operation=node.operation,
                            value=input_val,
                        )
                        file_content = result["value"]
                        
                        if isinstance(file_content, str):
                            if format_type:
                                file_content = self._deserialize_data(file_content, format_type)
                            elif serialize_json:
                                try:
                                    file_content = json.loads(file_content)
                                except json.JSONDecodeError:
                                    logger.warning(f"Failed to parse JSON from {file_path}")
                        
                        results[file_path] = file_content
                    except Exception as e:
                        logger.warning(f"Failed to read file {file_path}: {e}")
                        results[file_path] = None

                # Create output envelope for multiple files
                output_envelope = EnvelopeFactory.json(
                    results,
                    produced_by=node.id,
                    trace_id=trace_id
                ).with_meta(
                    multiple_files=True,
                    file_count=len(processed_paths),
                    format=format_type,
                    serialize_json=serialize_json,
                    glob=getattr(node, 'glob', False)
                )
                
                return output_envelope
            
            elif len(processed_paths) == 1:
                file_path = processed_paths[0]
                result = await db_service.execute_operation(
                    db_name=file_path,
                    operation=node.operation,
                    value=input_val,
                )

                if node.operation == "read":
                    output_value = result["value"]
                    if isinstance(output_value, str) and format_type:
                        output_value = self._deserialize_data(output_value, format_type)
                    elif isinstance(output_value, str) and getattr(node, 'serialize_json', False):
                        try:
                            output_value = json.loads(output_value)
                        except json.JSONDecodeError:
                            logger.warning(f"Failed to parse JSON from {file_path}")
                else:
                    meta = result["metadata"]
                    output_value = (
                        f"{node.operation.capitalize()}d to "
                        f"{meta['file_path']} ({meta.get('size', 0)} bytes)"
                    )

                serialize_json = getattr(node, 'serialize_json', False)
                
                # Create appropriate output envelope based on value type
                if isinstance(output_value, (dict, list)):
                    if serialize_json and not format_type:
                        # Serialize to text if requested
                        output_envelope = EnvelopeFactory.text(
                            json.dumps(output_value),
                            produced_by=node.id,
                            trace_id=trace_id
                        ).with_meta(
                            serialized=True,
                            original_type=type(output_value).__name__,
                            format=format_type
                        )
                    else:
                        # Return as JSON envelope
                        output_envelope = EnvelopeFactory.json(
                            output_value if isinstance(output_value, dict) else {"default": output_value},
                            produced_by=node.id,
                            trace_id=trace_id
                        ).with_meta(
                            wrapped_list=isinstance(output_value, list)
                        )
                else:
                    # Return as text envelope
                    output_envelope = EnvelopeFactory.text(
                        str(output_value),
                        produced_by=node.id,
                        trace_id=trace_id
                    )
                
                return output_envelope
            
            else:
                return EnvelopeFactory.error(
                    "No file paths specified for DB operation",
                    error_type="ValueError",
                    produced_by=str(node.id),
                    trace_id=trace_id
                )

        except Exception as exc:
            logger.exception("DB operation failed: %s", exc)
            return EnvelopeFactory.error(
                str(exc),
                error_type=exc.__class__.__name__,
                produced_by=str(node.id)
            )
