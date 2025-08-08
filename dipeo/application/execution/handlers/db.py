from __future__ import annotations

import glob
import json
import logging
import os
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.registry import DB_OPERATIONS_SERVICE
from dipeo.diagram_generated.generated_nodes import DBNode, NodeType
from dipeo.core.execution.node_output import TextOutput, ErrorOutput, DataOutput, NodeOutputProtocol
from dipeo.diagram_generated.models.db_model import DbNodeData as DBNodeData
from dipeo.application.utils.template import TemplateProcessor

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


@register_handler
class DBTypedNodeHandler(TypedNodeHandler[DBNode]):

    def __init__(self, db_operations_service: Any | None = None) -> None:
        self.db_operations_service = db_operations_service

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
        """Expand glob patterns in file paths."""
        expanded_paths = []
        
        for path in file_paths:
            # Check if path contains glob characters
            if any(char in path for char in ['*', '?', '[', ']']):
                # Handle relative paths with base_dir
                if base_dir and not os.path.isabs(path):
                    pattern = os.path.join(base_dir, path)
                else:
                    pattern = path
                
                # Expand glob pattern
                matches = glob.glob(pattern)
                if matches:
                    # If base_dir was used, convert back to relative paths
                    if base_dir and not os.path.isabs(path):
                        matches = [os.path.relpath(m, base_dir) for m in matches]
                    expanded_paths.extend(sorted(matches))
                else:
                    logger.warning(f"Glob pattern '{path}' matched no files")
            else:
                # Not a glob pattern, add as-is
                expanded_paths.append(path)
        
        return expanded_paths

    @staticmethod
    def _serialize_data(data: Any, format_type: str | None) -> str:
        """Serialize data according to the specified format."""
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
        """Deserialize data according to the specified format."""
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

    async def execute_request(self, request: ExecutionRequest[DBNode]) -> NodeOutputProtocol:
        # Extract properties from request
        node = request.node
        context = request.context
        inputs = request.inputs
        
        # Get service from ServiceRegistry
        db_service = request.services.resolve(DB_OPERATIONS_SERVICE)
        
        if db_service is None:
            raise RuntimeError("db_operations_service not available")
        
        # Handle file or list of files
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
                
                merged_variables = {**variables, **inputs}
                template_processor = TemplateProcessor()
                file_path = template_processor.process_single_brace(file_path, merged_variables)

            processed_paths.append(file_path)
        
        # Get format from node properties
        format_type = getattr(node, 'format', None)
        
        # Adjust file extensions based on format if needed
        if format_type and node.operation == "write":
            adjusted_paths = []
            for path in processed_paths:
                # Only adjust if no extension or wrong extension
                if format_type == 'yaml' and not path.endswith(('.yaml', '.yml')):
                    if '.' not in os.path.basename(path):
                        path = f"{path}.yaml"
                elif format_type == 'json' and not path.endswith('.json'):
                    if '.' not in os.path.basename(path):
                        path = f"{path}.json"
                adjusted_paths.append(path)
            processed_paths = adjusted_paths
        
        # Get base directory for relative path resolution
        base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
        
        # Expand glob patterns only if glob flag is true
        if getattr(node, 'glob', False):
            processed_paths = self._expand_glob_patterns(processed_paths, base_dir)

        if node.operation == "write":
            input_val = inputs.get('generated_code') or inputs.get('content') or inputs.get('value') or self._first_non_empty(inputs)
            if isinstance(input_val, dict):
                actual_content = input_val.get('generated_code') or input_val.get('content') or input_val.get('value')
                if actual_content is not None:
                    input_val = actual_content
            
            # Only serialize for YAML format or text format
            # JSON serialization is handled by db_adapter for consistency
            if node.operation == "write" and format_type == 'yaml' and input_val is not None:
                if isinstance(input_val, (dict, list)):
                    input_val = self._serialize_data(input_val, 'yaml')
            elif node.operation == "write" and format_type == 'text' and input_val is not None:
                if not isinstance(input_val, str):
                    input_val = str(input_val)
        else:
            input_val = self._first_non_empty(inputs)

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
                        
                        # Deserialize based on format or serialize_json flag
                        if isinstance(file_content, str):
                            if format_type:
                                file_content = self._deserialize_data(file_content, format_type)
                            elif serialize_json:
                                # Legacy support for serialize_json flag
                                try:
                                    file_content = json.loads(file_content)
                                except json.JSONDecodeError:
                                    logger.warning(f"Failed to parse JSON from {file_path}")
                        
                        results[file_path] = file_content
                    except Exception as e:
                        logger.warning(f"Failed to read file {file_path}: {e}")
                        results[file_path] = None

                return DataOutput(
                    value=results,
                    node_id=node.id,
                    metadata={
                        "multiple_files": True, 
                        "file_count": len(processed_paths), 
                        "format": format_type,
                        "serialize_json": serialize_json,
                        "glob": getattr(node, 'glob', False)
                    }
                )
            
            elif len(processed_paths) == 1:
                file_path = processed_paths[0]
                result = await db_service.execute_operation(
                    db_name=file_path,
                    operation=node.operation,
                    value=input_val,
                )

                if node.operation == "read":
                    output_value = result["value"]
                    # Deserialize based on format
                    if isinstance(output_value, str) and format_type:
                        output_value = self._deserialize_data(output_value, format_type)
                    # Legacy support for serialize_json flag
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

                # Return appropriate output type based on the value
                serialize_json = getattr(node, 'serialize_json', False)
                if isinstance(output_value, (dict, list)) and serialize_json and not format_type:
                    # Legacy behavior: serialize to JSON text when serialize_json is true
                    return TextOutput(
                        value=json.dumps(output_value),
                        node_id=node.id,
                        metadata={"serialized": True, "original_type": type(output_value).__name__, "format": format_type}
                    )
                elif isinstance(output_value, dict):
                    return DataOutput(
                        value=output_value,
                        node_id=node.id,
                        metadata={}
                    )
                elif isinstance(output_value, list):
                    return DataOutput(
                        value={"default": output_value},
                        node_id=node.id,
                        metadata={"wrapped_list": True}
                    )
                else:
                    return TextOutput(
                        value=str(output_value),
                        node_id=node.id,
                        metadata={}
                    )
            
            else:
                return ErrorOutput(
                    value="No file paths specified for DB operation",
                    node_id=node.id,
                    error_type="ValidationError"
                )

        except Exception as exc:
            logger.exception("DB operation failed: %s", exc)
            return ErrorOutput(
                value=f"DB operation failed: {exc}",
                node_id=node.id,
                error_type=type(exc).__name__
            )
