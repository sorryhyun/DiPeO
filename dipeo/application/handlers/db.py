"""DB node handler - file-based database operations."""

from typing import Any

from dipeo.application import BaseNodeHandler, register_handler
from dipeo.core.ports.execution_context import ExecutionContextPort
from dipeo.application.utils import create_node_output
from dipeo.models import DBNodeData, NodeOutput
from pydantic import BaseModel


@register_handler
class DBNodeHandler(BaseNodeHandler):
    """Handler for db nodes - delegates business logic to domain service."""
    
    def __init__(self, db_operations_service=None):
        """Initialize with injected services."""
        self.db_operations_service = db_operations_service


    @property
    def node_type(self) -> str:
        return "db"

    @property
    def schema(self) -> type[BaseModel]:
        return DBNodeData

    @property
    def requires_services(self) -> list[str]:
        return ["db_operations_service"]

    @property
    def description(self) -> str:
        return "File-based DB node supporting read, write and append operations"

    async def execute(
        self,
        props: DBNodeData,
        context: ExecutionContextPort,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute db node - delegates to domain service for validation and execution."""
        # Get service from context or fallback to services dict
        db_service = context.get_service("db_operations_service")
        if not db_service:
            db_service = services.get("db_operations_service")

        # Get single input value
        input_val = None
        if inputs:
            # Get first non-empty value
            for _key, val in inputs.items():
                if val is not None:
                    input_val = val
                    break

        try:
            # Delegate to domain service which handles validation and business logic
            result = await db_service.execute_operation(
                db_name=props.source_details, operation=props.operation, value=input_val
            )

            # Format output based on operation
            if props.operation == "read":
                output_value = result["value"]
            else:
                # For write/append, return a success message with metadata
                metadata = result["metadata"]
                output_value = f"{props.operation.capitalize()}d to {metadata['file_path']} ({metadata.get('size', 0)} bytes)"

            import logging

            log = logging.getLogger(__name__)
            log.debug(f"DB node output_value: {repr(output_value)}")
            return create_node_output(
                {"default": output_value},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )

        except Exception as exc:
            # Domain service throws specific validation errors
            error_msg = f"DB operation failed: {str(exc)}"
            return create_node_output(
                {"default": error_msg},
                metadata={"error": str(exc), "status": "failed"},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )