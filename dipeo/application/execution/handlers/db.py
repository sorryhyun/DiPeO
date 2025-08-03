from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
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

    async def execute(
        self,
        node: DBNode,
        context: "ExecutionContext",
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutputProtocol:
        # Get service from ServiceRegistry
        db_service = services.get(DB_OPERATIONS_SERVICE)
        
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

        if node.operation == "write":
            input_val = inputs.get('generated_code') or inputs.get('content') or inputs.get('value') or self._first_non_empty(inputs)
            if isinstance(input_val, dict):
                actual_content = input_val.get('generated_code') or input_val.get('content') or input_val.get('value')
                if actual_content is not None:
                    input_val = actual_content
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
                        
                        # Parse JSON if serialize_json is true
                        if serialize_json and isinstance(file_content, str):
                            import json
                            try:
                                file_content = json.loads(file_content)
                            except json.JSONDecodeError:
                                logger.warning(f"Failed to parse JSON from {file_path}")
                        
                        results[file_path] = file_content
                    except Exception as e:
                        logger.warning(f"Failed to read file {file_path}: {e}")
                        results[file_path] = None
                
                # Debug logging for multi-file read output
                logger.debug(f"DB {node.id} multi-file read returning dict with {len(results)} files")
                logger.debug(f"  File paths: {list(results.keys())[:3]}...")
                
                return DataOutput(
                    value=results,
                    node_id=node.id,
                    metadata={"multiple_files": True, "file_count": len(processed_paths), "serialize_json": serialize_json}
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
                else:
                    meta = result["metadata"]
                    output_value = (
                        f"{node.operation.capitalize()}d to "
                        f"{meta['file_path']} ({meta.get('size', 0)} bytes)"
                    )

                serialize_json = getattr(node, 'serialize_json', False)
                if isinstance(output_value, (dict, list)) and serialize_json:
                    import json
                    return TextOutput(
                        value=json.dumps(output_value),
                        node_id=node.id,
                        metadata={"serialized": True, "original_type": type(output_value).__name__}
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
