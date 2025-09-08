"""Single sub-diagram executor - handles execution of individual sub-diagrams."""

import logging
from typing import TYPE_CHECKING, Any

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handlers.sub_diagram.base_executor import BaseSubDiagramExecutor
from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase
from dipeo.diagram_generated import Status
from dipeo.diagram_generated.unified_nodes.sub_diagram_node import SubDiagramNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class SingleSubDiagramExecutor(BaseSubDiagramExecutor):
    """Executor for single sub-diagram execution with state tracking."""

    def __init__(self):
        """Initialize executor."""
        super().__init__()

    def set_services(self, state_store, message_router, diagram_service, service_registry=None):
        """Set services for the executor to use."""
        super().set_services(
            state_store=state_store,
            message_router=message_router,
            diagram_service=diagram_service,
            service_registry=service_registry,
        )

    async def execute(self, request: ExecutionRequest[SubDiagramNode]) -> Envelope:
        """Execute a single sub-diagram and return an Envelope.

        Returns an Envelope containing the execution results.
        """
        node = request.node
        trace_id = request.execution_id or ""

        try:
            # Use pre-configured services (set by handler)
            if not all([self._state_store, self._message_router, self._diagram_service]):
                raise ValueError("Required services not configured")

            # Load the diagram to execute
            domain_diagram = await self._load_diagram(node)

            # Prepare execution options
            # Don't pass parent inputs to sub-diagram by default to avoid contamination
            # Sub-diagrams should start with clean state unless explicitly configured
            options = {
                "variables": {},  # Empty variables by default
                "parent_execution_id": request.execution_id,
                "is_sub_diagram": True,
                "metadata": {"is_sub_diagram": True, "parent_execution_id": request.execution_id},
            }

            # Create a unique execution ID for the sub-diagram
            sub_execution_id = self._create_sub_execution_id(request.execution_id)

            # Create the execution use case
            execute_use_case = self._create_execution_use_case(request)

            # Configure event filter for sub-diagram execution
            event_filter = self._configure_event_filter(
                request=request, sub_execution_id=sub_execution_id, options=options
            )

            # Execute the sub-diagram and collect results
            execution_results, execution_error = await self._execute_sub_diagram(
                execute_use_case=execute_use_case,
                domain_diagram=domain_diagram,
                options=options,
                sub_execution_id=sub_execution_id,
                event_filter=event_filter,
            )

            # Build and return output
            return self._build_node_output(
                node=node,
                sub_execution_id=sub_execution_id,
                execution_results=execution_results,
                execution_error=execution_error,
            )

        except Exception as e:
            logger.error(f"Error executing sub-diagram node {node.id}: {e}", exc_info=True)
            error_data = {"error": str(e)}
            # Return error envelope directly
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
        """Create the execution use case with proper service registry."""
        from dipeo.application.execution.use_cases.execute_diagram import ExecuteDiagramUseCase

        # Get service registry and container
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

        # Create filter for sub-diagram execution
        event_filter = SubDiagramFilter(
            parent_execution_id=request.execution_id,
            propagate_to_sub=True,  # Allow sub-execution events
            scope_to_execution=False,  # Don't limit to parent only
        )

        # Log sub-diagram execution start
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
        """Build and return an Envelope with execution results.

        Creates an Envelope containing the execution results or error.
        """
        trace_id = sub_execution_id  # Use sub_execution_id as trace_id for continuity

        if execution_error:
            error_data = {"error": execution_error}
            # Return error envelope directly
            return EnvelopeFactory.create(
                body=error_data,
                produced_by=node.id,
                trace_id=trace_id,
                meta={"sub_execution_id": sub_execution_id, "execution_status": "failed"},
            )

        # Process output mapping
        output_value = self._process_output_mapping(node, execution_results)

        # Create envelope with auto-detection of content type
        envelope = EnvelopeFactory.create(
            body=output_value, produced_by=node.id, trace_id=trace_id, meta={}
        )

        # Add execution metadata to envelope
        return envelope.with_meta(
            sub_execution_id=sub_execution_id,
            execution_status="completed",
            diagram_name=node.diagram_name or "inline",
        )

    def _is_sub_diagram_context(self, request: ExecutionRequest[SubDiagramNode]) -> bool:
        """Check if we're running in a sub-diagram context."""
        # Check metadata for sub-diagram indicators
        if request.metadata and (
            request.metadata.get("parent_execution_id") or request.metadata.get("is_sub_diagram")
        ):
            return True

        # Check context metadata if available
        return (
            hasattr(request.context, "metadata")
            and request.context.metadata
            and (
                request.context.metadata.get("is_sub_diagram")
                or request.context.metadata.get("parent_execution_id")
            )
        )

    def _create_sub_execution_id(self, parent_execution_id: str) -> str:
        """Create a unique execution ID for sub-diagram."""
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
            # Process execution updates
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
            if data.get("status") == Status.COMPLETED.value:
                node_id = data.get("node_id")
                node_output = data.get("output")
                if node_id and node_output:
                    # Extract the actual value from Envelope if present
                    if hasattr(node_output, "value"):
                        execution_results[node_id] = node_output.value
                    else:
                        execution_results[node_id] = node_output
                    return {node_id: node_output}, None, False

        elif update_type == "EXECUTION_STATUS_CHANGED":
            data = update.get("data", {})
            if data.get("status") == Status.COMPLETED.value:
                return None, None, True
            elif data.get("status") == Status.FAILED.value:
                error = (
                    data.get("error")
                    or f"Execution failed (node_id: {data.get('node_id', 'unknown')})"
                )
                return None, error, True

        # Legacy support for old update types
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
