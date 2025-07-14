from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

from pydantic import BaseModel

from dipeo.application.execution import (
    UnifiedExecutionContext,
)
from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.types import TypedNodeHandler
from dipeo.core.static.generated_nodes import DBNode
from dipeo.models import DBNodeData, NodeOutput, NodeType

if TYPE_CHECKING:
    from dipeo.application.execution.simple_execution import SimpleExecution

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
    def _resolve_service(
        context: UnifiedExecutionContext,
        services: dict[str, Any],
        service_name: str,
    ) -> Any | None:
        """Try context first, fall back to the services mapping."""
        service = context.get_service(service_name)
        return service or services.get(service_name)

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

    async def pre_execute(
        self,
        node: DBNode,
        execution: SimpleExecution
    ) -> dict[str, Any]:
        """Pre-execute logic for DBNode."""
        return {
            "file": node.file,
            "collection": node.collection,
            "sub_type": node.sub_type.value if hasattr(node.sub_type, 'value') else node.sub_type,
            "operation": node.operation,
            "query": node.query,
            "data": node.data
        }
    
    async def execute(
        self,
        node: DBNode,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Run the DB operation with a strongly-typed `DBNode` instance."""
        db_service = self._resolve_service(context, services, "db_operations_service")
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
            return self._build_output(
                {"default": output_value},
                context,
            )

        except Exception as exc:
            logger.exception("DB operation failed: %s", exc)
            return self._build_output(
                {"default": f"DB operation failed: {exc}"},
                context,
                {"error": str(exc), "status": "failed"},
            )
