from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.unified_service_registry import DB_OPERATIONS_SERVICE
from dipeo.diagram_generated.generated_nodes import DBNode, NodeType
from dipeo.core.execution.node_output import TextOutput, ErrorOutput, DataOutput, NodeOutputProtocol
from dipeo.diagram_generated.models.db_model import DbNodeData as DBNodeData
from dipeo.application.utils.template import TemplateProcessor

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


@register_handler
class DBTypedNodeHandler(TypedNodeHandler[DBNode]):
    """
    File-based DB node supporting read, write and append operations.
    Mirrors the behaviour of the original DBNodeHandler, but with a
    strongly-typed `DBNode` instance supplied by the execution engine.
    """

    # ---------------------------------------------------------------------#
    #  Metadata                                                             #
    # ---------------------------------------------------------------------#

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

    # ---------------------------------------------------------------------#
    #  Helpers                                                              #
    # ---------------------------------------------------------------------#


    @staticmethod
    def _first_non_empty(inputs: dict[str, Any] | None) -> Any | None:
        if not inputs:
            return None
        for _k, v in inputs.items():
            if v is not None:
                return v
        return None

    # ---------------------------------------------------------------------#
    #  Typed execution                                                      #
    # ---------------------------------------------------------------------#
    async def execute(
        self,
        node: DBNode,
        context: "ExecutionContext",
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutputProtocol:
        """Run the DB operation with a strongly-typed `DBNode` instance."""
        # Get service from services dict
        db_service = services.get(DB_OPERATIONS_SERVICE.name)
        if db_service is None:  # Hard failure early
            raise RuntimeError("db_operations_service not available")
        
        # Handle file or list of files
        file_paths = node.file
        
        # Convert single file to list for uniform processing
        if isinstance(file_paths, str):
            file_paths = [file_paths]
        elif not file_paths:
            file_paths = []
        
        # Process placeholders in file paths
        processed_paths = []
        for file_path in file_paths:
            if file_path and '{' in file_path and '}' in file_path:
                # Get execution variables from context
                variables = {}
                if hasattr(context, 'get_variables'):
                    variables = context.get_variables()
                
                # Merge input values with context variables
                # Input values take precedence over context variables
                merged_variables = {**variables, **inputs}
                
                # Use TemplateProcessor to resolve single-brace placeholders
                template_processor = TemplateProcessor()
                file_path = template_processor.process_single_brace(file_path, merged_variables)
            
            processed_paths.append(file_path)

        # For write operations, prefer specific input keys
        if node.operation == "write":
            # Try common keys for write content
            input_val = inputs.get('generated_code') or inputs.get('content') or inputs.get('value') or self._first_non_empty(inputs)
            
            # If input_val is a dictionary, try to extract the actual content
            if isinstance(input_val, dict):
                # Try to extract the actual code/content from common keys
                actual_content = input_val.get('generated_code') or input_val.get('content') or input_val.get('value')
                if actual_content is not None:
                    input_val = actual_content
        else:
            input_val = self._first_non_empty(inputs)

        try:
            # Handle multiple file operations for read
            if node.operation == "read" and len(processed_paths) > 1:
                # Execute read operation for each file and collect results
                results = {}
                for file_path in processed_paths:
                    try:
                        result = await db_service.execute_operation(
                            db_name=file_path,
                            operation=node.operation,
                            value=input_val,
                        )
                        # Use the file path as key in results dictionary
                        results[file_path] = result["value"]
                    except Exception as e:
                        logger.warning(f"Failed to read file {file_path}: {e}")
                        results[file_path] = None
                
                # Return combined results as DataOutput
                return DataOutput(
                    value=results,
                    node_id=node.id,
                    metadata={"multiple_files": True, "file_count": len(processed_paths)}
                )
            
            # Single file operation (or write/append operations)
            elif len(processed_paths) == 1:
                file_path = processed_paths[0]
                result = await db_service.execute_operation(
                    db_name=file_path,
                    operation=node.operation,
                    value=input_val,
                )

                # ----------------- Format output ----------------- #
                if node.operation == "read":
                    output_value = result["value"]
                else:  # write / append
                    meta = result["metadata"]
                    output_value = (
                        f"{node.operation.capitalize()}d to "
                        f"{meta['file_path']} ({meta.get('size', 0)} bytes)"
                    )

                # Check if we should serialize to JSON for backward compatibility
                serialize_json = getattr(node, 'serialize_json', False)
                
                # Return appropriate output type based on data structure and serialization flag
                if isinstance(output_value, (dict, list)) and serialize_json:
                    # Backward compatibility: serialize to JSON string
                    import json
                    return TextOutput(
                        value=json.dumps(output_value),
                        node_id=node.id,
                        metadata={"serialized": True, "original_type": type(output_value).__name__}
                    )
                elif isinstance(output_value, dict):
                    # Return DataOutput for dict data
                    return DataOutput(
                        value=output_value,
                        node_id=node.id,
                        metadata={}
                    )
                elif isinstance(output_value, list):
                    # Wrap list in dict for DataOutput compatibility
                    return DataOutput(
                        value={"default": output_value},
                        node_id=node.id,
                        metadata={"wrapped_list": True}
                    )
                else:
                    # Return TextOutput for string data
                    return TextOutput(
                        value=str(output_value),
                        node_id=node.id,
                        metadata={}
                    )
            
            # No files specified
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
