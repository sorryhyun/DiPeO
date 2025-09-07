from __future__ import annotations

import glob
import json
import logging
import os
from typing import TYPE_CHECKING, Any

import yaml
from pydantic import BaseModel

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.registry import DB_OPERATIONS_SERVICE
from dipeo.diagram_generated.enums import NodeType
from dipeo.diagram_generated.unified_nodes.db_node import DbNode
from dipeo.domain.execution.envelope import Envelope, get_envelope_factory

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@register_handler
class DBTypedNodeHandler(TypedNodeHandler[DbNode]):
    """
    Clean separation of concerns using Template Method Pattern:
    1. validate() - Static/structural validation (compile-time checks)
    2. pre_execute() - Runtime validation and setup
    3. run() - Core execution logic
    4. serialize_output() - Custom envelope creation

    Now uses template method pattern to reduce code duplication.
    """

    NODE_TYPE = NodeType.DB.value

    def __init__(self) -> None:
        super().__init__()
        # Instance variables for passing data between methods
        self._current_db_service = None
        self._current_base_dir = None
        self._current_template_processor = None

    @property
    def node_class(self) -> type[DbNode]:
        return DbNode

    @property
    def schema(self) -> type[BaseModel]:
        return DbNode

    @property
    def requires_services(self) -> list[str]:
        return ["db_operations_service"]

    @property
    def description(self) -> str:
        return "File-based DB node supporting read, write and append operations"

    async def pre_execute(self, request: ExecutionRequest[DbNode]) -> Envelope | None:
        """Pre-execution setup: validate database service availability.

        Moves service resolution and validation out of execute_request
        for cleaner separation of concerns.
        """
        node = request.node

        # Resolve database operations service
        db_service = request.services.resolve(DB_OPERATIONS_SERVICE)

        if db_service is None:
            factory = get_envelope_factory()
            return factory.error(
                "Database operations service not available",
                error_type="ValueError",
                produced_by=str(node.id),
            )

        # Validate operation type
        valid_operations = ["read", "write", "append"]
        if node.operation not in valid_operations:
            factory = get_envelope_factory()
            return factory.error(
                f"Invalid operation: {node.operation}. Valid operations: {', '.join(valid_operations)}",
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

        # Store service and configuration in instance variables for execute_request
        self._current_db_service = db_service
        self._current_base_dir = os.getenv("DIPEO_BASE_DIR", os.getcwd())

        # Initialize template processor for path interpolation
        from dipeo.application.registry.keys import TEMPLATE_PROCESSOR

        template_processor = request.services.resolve(TEMPLATE_PROCESSOR)
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

        # Use pre-validated service and configuration from instance variables (set in pre_execute)
        db_service = self._current_db_service
        base_dir = self._current_base_dir
        template_processor = self._current_template_processor

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

        if format_type and node.operation == "write":
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

        if node.operation == "write":
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
            if node.operation == "write" and format_type == "yaml" and input_val is not None:
                if isinstance(input_val, dict | list):
                    input_val = self._serialize_data(input_val, "yaml")
            elif (
                node.operation == "write"
                and format_type == "text"
                and input_val is not None
                and not isinstance(input_val, str)
            ):
                input_val = str(input_val)
        else:
            input_val = self._first_non_empty(inputs)

        try:
            if node.operation == "read" and len(processed_paths) > 1:
                results = {}
                serialize_json = getattr(node, "serialize_json", False)
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

    def _format_as_table(self, query_result: Any) -> str:
        """Format query result as a simple text table."""
        if isinstance(query_result, dict):
            # For dict, format as key-value pairs
            lines = []
            for key, value in query_result.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
        elif isinstance(query_result, list):
            # For list, format as numbered items
            lines = []
            for i, item in enumerate(query_result):
                lines.append(f"{i+1}. {item}")
            return "\n".join(lines)
        else:
            return str(query_result)

    def _build_node_output(self, result: Any, request: ExecutionRequest[DbNode]) -> dict[str, Any]:
        """Build multi-representation output for database operations."""
        node = request.node
        operation = node.operation

        # Handle multiple files result
        if isinstance(result, dict) and "multiple_files" in result:
            file_count = result["file_count"]
            results = result["results"]

            representations = {
                "text": f"Read {file_count} files",
                "object": results,
                "metadata": {
                    "affected_rows": file_count,
                    "operation": operation,
                    "file_count": file_count,
                    "format": result.get("format"),
                    "glob": result.get("glob", False),
                },
            }

            return {
                "primary": results,
                "representations": representations,
                "meta": {
                    "multiple_files": True,
                    "file_count": file_count,
                    "format": result.get("format"),
                    "serialize_json": result.get("serialize_json", False),
                    "glob": result.get("glob", False),
                },
            }

        # Handle single file result
        if isinstance(result, dict) and "value" in result:
            output_value = result["value"]

            # Build representations
            representations = {
                "text": self._format_as_table(output_value)
                if isinstance(output_value, dict | list)
                else str(output_value),
                "object": output_value,
                "metadata": {
                    "affected_rows": 1
                    if operation == "write"
                    else len(output_value)
                    if isinstance(output_value, list | dict)
                    else 1,
                    "operation": operation,
                    "format": result.get("format"),
                },
            }

            # Determine primary value based on type
            if isinstance(output_value, dict | list):
                if result.get("serialize_json", False) and not result.get("format"):
                    # Serialize to text if requested
                    primary = json.dumps(output_value)
                    primary_type = "text"
                else:
                    # Keep as structured data
                    primary = (
                        output_value
                        if isinstance(output_value, dict)
                        else {"default": output_value}
                    )
                    primary_type = "json"
            else:
                primary = str(output_value)
                primary_type = "text"

            return {
                "primary": primary,
                "primary_type": primary_type,
                "representations": representations,
                "meta": {
                    "operation": operation,
                    "format": result.get("format"),
                    "serialize_json": result.get("serialize_json", False),
                },
            }

        # Fallback for unexpected result format
        return {
            "primary": result,
            "primary_type": "text",
            "representations": {
                "text": str(result),
                "object": result,
                "metadata": {"operation": operation},
            },
            "meta": {"operation": operation},
        }

    def serialize_output(self, result: Any, request: ExecutionRequest[DbNode]) -> Envelope:
        """Custom serialization for DB results with multi-representation."""
        node = request.node
        trace_id = request.execution_id or ""
        factory = get_envelope_factory()

        # Build multi-representation output
        output = self._build_node_output(result, request)

        # Create envelope based on primary type
        primary = output["primary"]
        primary_type = output.get("primary_type", "text")

        if primary_type == "json":
            envelope = factory.json(primary, produced_by=node.id, trace_id=trace_id)
        else:
            envelope = factory.text(str(primary), produced_by=node.id, trace_id=trace_id)

        # Add representations
        if "representations" in output:
            envelope = envelope.with_representations(output["representations"])

        # Add metadata
        if "meta" in output:
            envelope = envelope.with_meta(**output["meta"])

        return envelope

    async def prepare_inputs(
        self, request: ExecutionRequest[DbNode], inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Prepare inputs with token consumption.

        Phase 5: Now consumes tokens from incoming edges when available.
        """
        # Phase 5: Consume tokens from incoming edges or fall back to regular inputs
        envelope_inputs = self.consume_token_inputs(request, inputs)

        # Call parent prepare_inputs for default envelope conversion
        return await super().prepare_inputs(request, envelope_inputs)

    def post_execute(self, request: ExecutionRequest[DbNode], output: Envelope) -> Envelope:
        """Post-execution hook to emit tokens.

        Phase 5: Now emits output as tokens to trigger downstream nodes.
        """
        # Phase 5: Emit output as tokens to trigger downstream nodes
        self.emit_token_outputs(request, output)

        return output
