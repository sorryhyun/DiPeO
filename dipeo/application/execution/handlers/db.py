from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.unified_service_registry import DB_OPERATIONS_SERVICE
from dipeo.core.static.generated_nodes import DBNode
from dipeo.core.execution.node_output import TextOutput, ErrorOutput, DataOutput, NodeOutputProtocol
from dipeo.models import DBNodeData, NodeType

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
        return NodeType.db.value

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

        input_val = self._first_non_empty(inputs)

        try:
            result = await db_service.execute_operation(
                db_name=node.file,
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

            logger.debug("DB node output_value: %s", repr(output_value))
            
            # Convert structured data to JSON string for consistent handling
            if isinstance(output_value, (dict, list)):
                import json
                return TextOutput(
                    value=json.dumps(output_value),
                    node_id=node.id,
                    metadata={"serialized": True, "original_type": type(output_value).__name__}
                )
            else:
                return TextOutput(
                    value=str(output_value),
                    node_id=node.id,
                    metadata={}
                )

        except Exception as exc:
            logger.exception("DB operation failed: %s", exc)
            return ErrorOutput(
                value=f"DB operation failed: {exc}",
                node_id=node.id,
                error_type=type(exc).__name__
            )
