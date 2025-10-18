"""Single sub-diagram executor - handles execution of individual sub-diagrams."""

from typing import TYPE_CHECKING, Any

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import Status
from dipeo.diagram_generated.unified_nodes.sub_diagram_node import SubDiagramNode
from dipeo.domain.execution.messaging.envelope import Envelope, EnvelopeFactory

from .base_executor import BaseSubDiagramExecutor

if TYPE_CHECKING:
    pass

logger = get_module_logger(__name__)


class SingleSubDiagramExecutor(BaseSubDiagramExecutor):
    """Executor for single sub-diagram execution with state tracking."""

    def __init__(self):
        super().__init__()

    def set_services(
        self, state_store, message_router, diagram_service, service_registry=None, event_bus=None
    ):
        super().set_services(
            state_store=state_store,
            message_router=message_router,
            diagram_service=diagram_service,
            service_registry=service_registry,
            event_bus=event_bus,
        )

    async def execute(self, request: ExecutionRequest[SubDiagramNode]) -> Envelope:
        """Execute a single sub-diagram with state tracking."""
        node = request.node
        trace_id = request.execution_id or ""

        try:
            if not all([self._state_store, self._message_router, self._diagram_service]):
                raise ValueError("Required services not configured")

            domain_diagram = await self._load_diagram(node)

            # Don't pass parent inputs to sub-diagram by default to avoid contamination
            options = {
                "variables": {},
                "parent_execution_id": request.execution_id,
                "is_sub_diagram": True,
                "metadata": {"is_sub_diagram": True, "parent_execution_id": request.execution_id},
            }

            sub_execution_id = self._create_sub_execution_id(request.execution_id)

            execute_use_case = self._create_execution_use_case(request)

            event_filter = self._configure_event_filter(
                request=request, sub_execution_id=sub_execution_id, options=options
            )

            execution_results, execution_error = await self._execute_sub_diagram(
                execute_use_case=execute_use_case,
                domain_diagram=domain_diagram,
                options=options,
                sub_execution_id=sub_execution_id,
                event_filter=event_filter,
            )

            return self._build_node_output(
                node=node,
                sub_execution_id=sub_execution_id,
                execution_results=execution_results,
                execution_error=execution_error,
            )

        except Exception as e:
            logger.error(f"Error executing sub-diagram node {node.id}: {e}", exc_info=True)
            error_data = {"error": str(e)}
            return EnvelopeFactory.create(
                body=error_data,
                produced_by=node.id,
                trace_id=trace_id,
                error=type(e).__name__,
                meta={"execution_status": "failed"},
            )

    def _create_execution_use_case(
        self, request: ExecutionRequest[SubDiagramNode]
    ) -> ExecuteDiagramUseCase:
        service_registry = request.parent_registry
        if not service_registry:
            from dipeo.application.registry import ServiceKey, ServiceRegistry

            service_registry = ServiceRegistry()
            for service_name, service in request.services.items():
                key = ServiceKey(service_name)
                service_registry.register(key, service)

        container = request.parent_container

        return ExecuteDiagramUseCase(
            service_registry=service_registry,
            state_store=self._state_store,
            message_router=self._message_router,
            diagram_service=self._diagram_service,
            container=container,
        )

    def _configure_event_filter(
        self,
        request: ExecutionRequest[SubDiagramNode],
        sub_execution_id: str,
        options: dict[str, Any],
    ) -> Any:
        """Configure event filter for sub-diagram execution.

        Returns an EventFilter that scopes events to the sub-diagram execution.
        """
        from dipeo.domain.events import SubDiagramFilter

        event_filter = SubDiagramFilter(
            parent_execution_id=request.execution_id,
            propagate_to_sub=True,
            scope_to_execution=False,
        )

        if request.metadata:
            request.add_metadata("sub_execution_id", sub_execution_id)

        return event_filter

    def _build_node_output(
        self,
        node: SubDiagramNode,
        sub_execution_id: str,
        execution_results: dict[str, Any],
        execution_error: str | None,
    ) -> Envelope:
        """Build an Envelope with execution results or error."""
        trace_id = sub_execution_id

        if execution_error:
            error_data = {"error": execution_error}
            return EnvelopeFactory.create(
                body=error_data,
                produced_by=node.id,
                trace_id=trace_id,
                meta={"sub_execution_id": sub_execution_id, "execution_status": "failed"},
            )

        output_value = self._process_output_mapping(node, execution_results)

        envelope = EnvelopeFactory.create(
            body=output_value, produced_by=node.id, trace_id=trace_id, meta={}
        )

        return envelope.with_meta(
            sub_execution_id=sub_execution_id,
            execution_status="completed",
            diagram_name=node.diagram_name or "inline",
        )

    def _is_sub_diagram_context(self, request: ExecutionRequest[SubDiagramNode]) -> bool:
        if request.metadata and (
            request.metadata.get("parent_execution_id") or request.metadata.get("is_sub_diagram")
        ):
            return True

        return (
            hasattr(request.context, "metadata")
            and request.context.metadata
            and (
                request.context.metadata.get("is_sub_diagram")
                or request.context.metadata.get("parent_execution_id")
            )
        )

    def _create_sub_execution_id(self, parent_execution_id: str) -> str:
        return self._create_execution_id(parent_execution_id, "sub")

    async def _execute_sub_diagram(
        self,
        execute_use_case: "ExecuteDiagramUseCase",
        domain_diagram: Any,  # DomainDiagram
        options: dict[str, Any],
        sub_execution_id: str,
        event_filter: Any,
    ) -> tuple[dict[str, Any], str | None]:
        """Execute the sub-diagram and return results and any error.

        Processes execution updates and extracts node outputs, which may include envelopes.
        """
        execution_results = {}
        execution_error = None

        async for update in execute_use_case.execute_diagram(
            diagram=domain_diagram,
            options=options,
            execution_id=sub_execution_id,
            interactive_handler=None,
            event_filter=event_filter,
        ):
            result, error, should_break = self._process_execution_update(update, execution_results)

            if error:
                execution_error = error
                logger.error(f"Sub-diagram execution failed: {execution_error}")

            if should_break:
                break

        return execution_results, execution_error

    def _process_execution_update(
        self, update: dict[str, Any], execution_results: dict[str, Any]
    ) -> tuple[dict | None, str | None, bool]:
        """Process a single execution update.

        Handles both envelope-based and legacy outputs from sub-diagram nodes.

        Returns: (result, error, should_break)
        """
        update_type = update.get("type", "")

        if update_type == "NODE_STATUS_CHANGED":
            data = update.get("data", {})
            if data.get("status") == Status.COMPLETED:
                node_id = data.get("node_id")
                node_output = data.get("output")
                if node_id and node_output:
                    if hasattr(node_output, "value"):
                        execution_results[node_id] = node_output.value
                    else:
                        execution_results[node_id] = node_output
                    return {node_id: node_output}, None, False

        elif update_type in ["EXECUTION_COMPLETED", "execution_completed"]:
            return None, None, True
        elif update_type in ["EXECUTION_ERROR", "execution_error"]:
            data = update.get("data", {})
            error = (
                data.get("error") or f"Execution failed (node_id: {data.get('node_id', 'unknown')})"
            )
            return None, error, True

        elif update_type == "node_complete":
            node_id = update.get("node_id")
            node_output = update.get("output")
            if node_id and node_output:
                execution_results[node_id] = node_output
                return {node_id: node_output}, None, False

        elif update_type == "execution_complete":
            return None, None, True

        elif update_type == "execution_error":
            error = (
                update.get("error")
                or f"Execution failed with status: {update.get('status', 'unknown')}"
            )
            return None, error, True

        return None, None, False
