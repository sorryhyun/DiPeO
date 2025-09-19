from __future__ import annotations

import glob
import json
import logging
import os
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handlers.core.base import TypedNodeHandler
from dipeo.application.execution.handlers.core.decorators import Optional, requires_services
from dipeo.application.execution.handlers.core.factory import register_handler
from dipeo.application.registry import DB_OPERATIONS_SERVICE
from dipeo.application.registry.keys import TEMPLATE_PROCESSOR
from dipeo.config.paths import BASE_DIR
from dipeo.diagram_generated.enums import NodeType
from dipeo.diagram_generated.unified_nodes.db_node import DbNode
from dipeo.domain.execution.envelope import Envelope, get_envelope_factory

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@register_handler
@requires_services(
    db_service=DB_OPERATIONS_SERVICE,
    template_processor=(TEMPLATE_PROCESSOR, Optional),
)
class DBTypedNodeHandler(TypedNodeHandler[DbNode]):
    """File-based DB node supporting read, write and append operations."""

    NODE_TYPE = NodeType.DB.value

    def __init__(self) -> None:
        super().__init__()
        self._current_base_dir = None

    @property
    def node_class(self) -> type[DbNode]:
        return DbNode

    @property
    def schema(self) -> type[BaseModel]:
        return DbNode

    @property
    def description(self) -> str:
        return "File-based DB node supporting read, write and append operations"

    async def pre_execute(self, request: ExecutionRequest[DbNode]) -> Envelope | None:
        """Pre-execution setup: validate operation configuration."""
        node = request.node

        # Validate operation type
        valid_operations = ["read", "write", "append", "update"]
        if node.operation not in valid_operations:
            factory = get_envelope_factory()
            return factory.error(
                f"Invalid operation: {node.operation}. Valid operations: {', '.join(valid_operations)}",
                error_type="ValueError",
                produced_by=str(node.id),
            )

        if node.operation == "update" and not getattr(node, "keys", None):
            factory = get_envelope_factory()
            return factory.error(
                "Update operation requires one or more keys",
                error_type="ValueError",
                produced_by=str(node.id),
            )

        # Validate file paths are provided
        file_paths = node.file
        if not file_paths:
            factory = get_envelope_factory()
            return factory.error(
                "No file paths specified for database operation",
                error_type="ValueError",
                produced_by=str(node.id),
            )

        # Store configuration in instance variables for execute_request
        self._current_base_dir = str(BASE_DIR)

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
            if any(char in path for char in ["*", "?", "[", "]"]):
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
        if format_type == "json":
            return json.dumps(data, indent=2)
        elif format_type == "yaml":
            return yaml.dump(data, default_flow_style=False)
        elif format_type == "text" or format_type is None:
            return str(data)
        else:
            logger.warning(f"Unknown format '{format_type}', using text format")
            return str(data)

    @staticmethod
    def _deserialize_data(content: str, format_type: str | None) -> Any:
        if not content:
            return content

        if format_type == "json":
            try:
                return json.loads(content)
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON: {e}")
                return content
        elif format_type == "yaml":
            try:
                return yaml.safe_load(content)
            except yaml.YAMLError as e:
                logger.warning(f"Failed to parse YAML: {e}")
                return content
        elif format_type == "text" or format_type is None:
            return content
        else:
            logger.warning(f"Unknown format '{format_type}', returning as text")
            return content

    async def run(self, inputs: dict[str, Any], request: ExecutionRequest[DbNode]) -> Any:
        """Execute database operation."""
        node = request.node
        context = request.context

        # Services are injected by decorator
        db_service = self._db_service
        template_processor = self._template_processor
        base_dir = self._current_base_dir

        file_paths = node.file

        if isinstance(file_paths, str):
            file_paths = [file_paths]
        elif not file_paths:
            file_paths = []

        # Use PromptBuilder to properly prepare template values from inputs
        # This handles nested structures and makes node outputs available
        from dipeo.application.utils import PromptBuilder

        prompt_builder = PromptBuilder(template_processor)
        prepared_inputs = prompt_builder.prepare_template_values(inputs)

        # Use centralized context builder to merge globals properly
        template_values = context.build_template_context(inputs=prepared_inputs, globals_win=True)

        processed_paths = []
        for file_path in file_paths:
            if file_path and "{" in file_path and "}" in file_path:
                if template_processor:
                    resolved_path = template_processor.process_single_brace(
                        file_path, template_values
                    )
                    file_path = resolved_path
                else:
                    logger.warning(f"No template processor available for path: {file_path}")

            processed_paths.append(file_path)

        # Auto-detect and expand glob patterns before passing to db_service
        # No need for explicit glob field - just check if paths contain glob characters
        processed_paths = self._expand_glob_patterns(processed_paths, base_dir)

        format_type = getattr(node, "format", None)

        if format_type and node.operation in ("write", "update"):
            adjusted_paths = []
            for path in processed_paths:
                if format_type == "yaml" and not path.endswith((".yaml", ".yml")):
                    if "." not in os.path.basename(path):
                        path = f"{path}.yaml"
                elif (
                    format_type == "json"
                    and not path.endswith(".json")
                    and "." not in os.path.basename(path)
                ):
                    path = f"{path}.json"
                adjusted_paths.append(path)
            processed_paths = adjusted_paths

        if node.operation in ("write", "update"):
            input_val = (
                inputs.get("generated_code")
                or inputs.get("content")
                or inputs.get("value")
                or self._first_non_empty(inputs)
            )
            if isinstance(input_val, dict):
                actual_content = (
                    input_val.get("generated_code")
                    or input_val.get("content")
                    or input_val.get("value")
                )
                if actual_content is not None:
                    input_val = actual_content

            # Only serialize for YAML format or text format
            # JSON serialization is handled by db_adapter
            if (
                node.operation in ("write", "update")
                and format_type == "yaml"
                and input_val is not None
            ):
                if isinstance(input_val, dict | list):
                    input_val = self._serialize_data(input_val, "yaml")
            elif (
                node.operation in ("write", "update")
                and format_type == "text"
                and input_val is not None
                and not isinstance(input_val, str)
            ):
                input_val = str(input_val)
        else:
            input_val = self._first_non_empty(inputs)

        try:
            keys = getattr(node, "keys", None)

            if node.operation == "read" and len(processed_paths) > 1:
                results = {}
                serialize_json = getattr(node, "serialize_json", False)
                for file_path in processed_paths:
                    try:
                        result = await db_service.execute_operation(
                            db_name=file_path,
                            operation=node.operation,
                            value=input_val,
                            keys=keys,
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

                # Return raw results - will be serialized by serialize_output
                return {
                    "results": results,
                    "multiple_files": True,
                    "file_count": len(processed_paths),
                    "format": format_type,
                    "serialize_json": serialize_json,
                }

            elif len(processed_paths) == 1:
                file_path = processed_paths[0]
                result = await db_service.execute_operation(
                    db_name=file_path,
                    operation=node.operation,
                    value=input_val,
                    keys=keys,
                )

                if node.operation == "read":
                    output_value = result["value"]
                    if isinstance(output_value, str) and format_type:
                        output_value = self._deserialize_data(output_value, format_type)
                    elif isinstance(output_value, str) and getattr(node, "serialize_json", False):
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

                serialize_json = getattr(node, "serialize_json", False)

                # Return raw result with metadata
                return {
                    "value": output_value,
                    "serialize_json": serialize_json,
                    "format": format_type,
                    "operation": node.operation,
                }

            else:
                raise ValueError("No file paths specified for DB operation")

        except Exception as exc:
            logger.exception("DB operation failed: %s", exc)
            raise  # Let base class handle error

    def serialize_output(self, result: Any, request: ExecutionRequest[DbNode]) -> Envelope:
        """Custom serialization for DB results."""
        node = request.node
        trace_id = request.execution_id or ""
        factory = get_envelope_factory()
        operation = node.operation

        # Handle multiple files result
        if isinstance(result, dict) and "multiple_files" in result:
            file_count = result["file_count"]
            results = result["results"]

            # Create envelope with results as body
            envelope = factory.create(body=results, produced_by=node.id, trace_id=trace_id)

            # Add metadata about the operation
            envelope = envelope.with_meta(
                multiple_files=True,
                file_count=file_count,
                operation=operation,
                format=result.get("format"),
                serialize_json=result.get("serialize_json", False),
                glob=result.get("glob", False),
            )

            return envelope

        # Handle single file result
        if isinstance(result, dict) and "value" in result:
            output_value = result["value"]

            # Determine the body based on serialize_json flag
            if isinstance(output_value, dict | list):
                if result.get("serialize_json", False) and not result.get("format"):
                    # Serialize to text if requested
                    body = json.dumps(output_value)
                else:
                    # Keep as structured data
                    body = output_value
            else:
                body = output_value

            # Create envelope
            envelope = factory.create(body=body, produced_by=node.id, trace_id=trace_id)

            # Add metadata
            envelope = envelope.with_meta(
                operation=operation,
                format=result.get("format"),
                serialize_json=result.get("serialize_json", False),
            )

            return envelope

        # Fallback for unexpected result format
        envelope = factory.create(body=result, produced_by=node.id, trace_id=trace_id)

        envelope = envelope.with_meta(operation=operation)

        return envelope

    async def prepare_inputs(
        self, request: ExecutionRequest[DbNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Prepare inputs with token consumption.

        Phase 5: Now consumes tokens from incoming edges when available.
        """
        # Phase 5: Consume tokens from incoming edges or fall back to regular inputs
        envelope_inputs = self.get_effective_inputs(request, inputs)

        # Call parent prepare_inputs for default envelope conversion
        return await super().prepare_inputs(request, envelope_inputs)

    def post_execute(self, request: ExecutionRequest[DbNode], output: Envelope) -> Envelope:
        """Post-execution hook to emit tokens.

        Phase 5: Now emits output as tokens to trigger downstream nodes.
        """
        # Phase 5: Emit output as tokens to trigger downstream nodes
        self.emit_token_outputs(request, output)

        return output
