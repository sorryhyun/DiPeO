"""Lightweight sub-diagram executor that runs without state persistence.

This executor treats sub-diagrams as running "inside" the parent node,
without creating separate execution contexts or state persistence.
"""

import contextlib
import copy
import logging
import os
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.application.execution.engine.typed_engine import TypedExecutionEngine
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import ExecutionID, ExecutionState, LLMUsage, NodeState, Status
from dipeo.diagram_generated.unified_nodes.sub_diagram_node import SubDiagramNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.infrastructure.events.adapters import InMemoryEventBus

from .base_executor import BaseSubDiagramExecutor
from .parallel_executor import ParallelExecutionManager

if TYPE_CHECKING:
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram

logger = get_module_logger(__name__)


class LightweightSubDiagramExecutor(BaseSubDiagramExecutor):
    """Executes sub-diagrams without state persistence, treating them as internal node operations."""

    def __init__(self):
        super().__init__()
        self._parallel_manager: ParallelExecutionManager | None = None
        self._fail_fast = os.getenv("DIPEO_FAIL_FAST", "false").lower() == "true"

    def set_services(
        self, prepare_use_case, diagram_service, service_registry=None, event_bus=None
    ):
        super().set_services(
            prepare_use_case=prepare_use_case,
            diagram_service=diagram_service,
            service_registry=service_registry,
            event_bus=event_bus,
        )

    async def execute(self, request: ExecutionRequest[SubDiagramNode]) -> Envelope:
        """Execute a sub-diagram in lightweight mode without state persistence.

        Returns an Envelope containing the execution results.
        """
        node = request.node
        trace_id = request.execution_id or ""

        request.metadata["is_sub_diagram"] = True
        request.metadata["parent_diagram"] = node.diagram_name or "inline"

        try:
            executable_diagram = await self._prepare_diagram(node, request)

            sub_diagram_inputs = {}
            if getattr(node, "passInputData", False):
                sub_diagram_inputs = request.inputs if hasattr(request, "inputs") else {}

            if getattr(node, "input_mapping", None):
                mapped_inputs = {}
                for target_key, source_key in node.input_mapping.items():
                    if source_key in (request.inputs if hasattr(request, "inputs") else {}):
                        mapped_inputs[target_key] = request.inputs[source_key]
                sub_diagram_inputs = mapped_inputs

            execution_state = self._create_in_memory_state(
                diagram=executable_diagram,
                inputs=sub_diagram_inputs,
            )

            execution_results, execution_errors = await self._run_lightweight_execution(
                diagram=executable_diagram, execution_state=execution_state, request=request
            )

            if self._fail_fast and execution_errors:
                first_error = execution_errors[0]
                logger.error(
                    f"Fail-fast triggered in sub-diagram '{node.diagram_name}' "
                    f"(node: {node.id}): {first_error['error']}"
                )
                return self._create_error_envelope(
                    node=node,
                    trace_id=trace_id,
                    error_message=first_error["error"],
                    error_type="SubDiagramFailFastError",
                    execution_errors=execution_errors,
                )

            return self._build_node_output(
                node=node,
                execution_results=execution_results,
                trace_id=trace_id,
                execution_errors=execution_errors,
            )

        except Exception as e:
            logger.error(
                f"Error in lightweight sub-diagram execution for node {node.id}: {e}", exc_info=True
            )
            return self._create_error_envelope(
                node=node, trace_id=trace_id, error_message=str(e), error_type=type(e).__name__
            )

    async def _prepare_diagram(
        self, node: SubDiagramNode, request: ExecutionRequest
    ) -> "ExecutableDiagram":
        """Prepare the diagram for execution (load and compile)."""
        if self._prepare_use_case:
            diagram_input = await self._get_diagram_input(node)

            diagram_id = None
            if node.diagram_name:
                diagram_id = self._construct_diagram_path(node)

            return await self._prepare_use_case.prepare_for_execution(
                diagram=diagram_input,
                diagram_id=diagram_id,
                validate=False,
            )
        else:
            logger.warning(
                "PrepareDiagramForExecutionUseCase not found, using fallback implementation"
            )
            diagram_data = await self._load_diagram_fallback(node)
            return await self._compile_diagram_fallback(diagram_data)

    async def _get_diagram_input(self, node: SubDiagramNode) -> Any:
        """Get the diagram input for preparation.

        Returns either diagram_data dict, a DomainDiagram, or a string ID/path.
        """
        if node.diagram_data:
            return node.diagram_data

        if not node.diagram_name:
            raise ValueError("No diagram specified for execution")

        file_path = self._construct_diagram_path(node)

        if self._diagram_service:
            try:
                diagram = await self._diagram_service.load_from_file(file_path)
                return diagram
            except Exception as e:
                logger.error(f"Error loading diagram from '{file_path}': {e!s}")
                return file_path
        else:
            return file_path

    async def _load_diagram_fallback(self, node: SubDiagramNode) -> Any:
        if node.diagram_data:
            return node.diagram_data

        if not node.diagram_name:
            raise ValueError("No diagram specified for execution")

        if not self._diagram_service:
            raise ValueError("Diagram service not available")

        file_path = self._construct_diagram_path(node)

        try:
            diagram = await self._diagram_service.load_from_file(file_path)
            return diagram
        except Exception as e:
            logger.error(f"Error loading diagram from '{file_path}': {e!s}")
            raise ValueError(f"Failed to load diagram '{node.diagram_name}': {e!s}") from e

    async def _compile_diagram_fallback(self, diagram_data: Any) -> "ExecutableDiagram":
        from dipeo.diagram_generated import DomainDiagram
        from dipeo.infrastructure.diagram.adapters import StandardCompilerAdapter

        if isinstance(diagram_data, DomainDiagram):
            domain_diagram = diagram_data
        elif isinstance(diagram_data, dict):
            domain_diagram = DomainDiagram.model_validate(diagram_data)
        else:
            raise ValueError(f"Unsupported diagram type: {type(diagram_data)}")

        compiler = StandardCompilerAdapter(use_interface_based=True)
        executable_diagram = compiler.compile(domain_diagram)

        return executable_diagram

    def _create_in_memory_state(
        self, diagram: "ExecutableDiagram", inputs: dict[str, Any]
    ) -> ExecutionState:
        """Create a minimal in-memory execution state.

        Uses deep-copy isolation: each sub-diagram gets a completely separate execution
        context with deep-copied variables, preventing variable pollution between parent
        and child executions. Only explicitly declared outputs are returned to parent.
        """
        node_states = {}
        all_nodes = diagram.get_nodes_by_type(None) or diagram.nodes
        for node in all_nodes:
            node_state = NodeState(
                status=Status.PENDING,
                started_at=None,
                ended_at=None,
                output=None,
                error=None,
                llm_usage=None,
            )
            node_states[str(node.id)] = node_state

        # Deep-copy variables to isolate from parent
        variables = {}
        if inputs:
            if "default" in inputs and isinstance(inputs["default"], dict):
                variables = copy.deepcopy(inputs["default"])
            elif inputs:
                variables = copy.deepcopy(inputs)

        execution_state = ExecutionState(
            id=ExecutionID(f"lightweight_{uuid.uuid4().hex[:8]}"),
            diagram_id=diagram.id if hasattr(diagram, "id") else "unknown",
            status=Status.PENDING,
            started_at=datetime.now(UTC).isoformat(),
            node_states=node_states,
            node_outputs={},
            llm_usage=LLMUsage(input=0, output=0, total=0),
            exec_counts={},
            executed_nodes=[],
            variables=variables,
        )

        return execution_state

    async def _run_lightweight_execution(
        self,
        diagram: "ExecutableDiagram",
        execution_state: ExecutionState,
        request: ExecutionRequest,
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Run the execution engine without state persistence.

        Returns:
            Tuple of (execution_results, execution_errors)
        """

        parent_registry = request.parent_registry or request.services
        isolated_registry = self._create_isolated_registry(parent_registry)

        await self._register_diagram_persons(diagram, isolated_registry)

        # Use parent event bus if available to ensure metrics are captured
        # If no parent event bus is available, fall back to InMemoryEventBus
        event_bus = self._event_bus if self._event_bus else InMemoryEventBus()

        engine = TypedExecutionEngine(
            service_registry=isolated_registry,
            event_bus=event_bus,
        )

        execution_results = {}
        execution_errors = []

        async for update in engine.execute(
            diagram=diagram,
            execution_state=execution_state,
            options={
                "is_lightweight": True,
                "parent_node_id": str(request.node.id),
                "parent_metadata": request.metadata,
                "parent_execution_id": request.execution_id,
            },
            container=request.parent_container,
            interactive_handler=None,
        ):
            self._process_execution_update(
                update, execution_state, execution_results, execution_errors
            )

            if self._fail_fast and execution_errors:
                logger.warning("Fail-fast triggered, stopping execution of sub-diagram")
                break

        self._collect_final_outputs(execution_state, execution_results, execution_errors)

        return execution_results, execution_errors

    def _process_execution_update(
        self,
        update: dict[str, Any],
        execution_state: ExecutionState,
        execution_results: dict[str, Any],
        execution_errors: list[dict[str, Any]],
    ) -> None:
        """Process execution updates and collect completed outputs and errors.

        Handles both envelope-based and legacy outputs from nodes.
        """
        if update.get("type") == "step_complete":
            for node_id_str, node_state in execution_state.node_states.items():
                if node_state.status == Status.COMPLETED and node_state.output:
                    if node_id_str not in execution_results:
                        output = node_state.output
                        if hasattr(output, "value"):
                            execution_results[node_id_str] = output.value
                        else:
                            execution_results[node_id_str] = output
                elif node_state.status == Status.FAILED:
                    error_info = {
                        "node_id": node_id_str,
                        "error": str(node_state.error) if node_state.error else "Unknown error",
                        "status": "failed",
                    }
                    if error_info not in execution_errors:
                        execution_errors.append(error_info)

    def _collect_final_outputs(
        self,
        execution_state: ExecutionState,
        execution_results: dict[str, Any],
        execution_errors: list[dict[str, Any]],
    ) -> None:
        """Collect any remaining outputs and errors after execution completes.

        Handles both envelope-based and legacy outputs from nodes.
        """
        for node_id_str, node_state in execution_state.node_states.items():
            if node_state.status == Status.COMPLETED and node_state.output:
                if node_id_str not in execution_results:
                    output = node_state.output
                    if hasattr(output, "value"):
                        execution_results[node_id_str] = output.value
                    else:
                        execution_results[node_id_str] = output
            elif node_state.status == Status.FAILED:
                error_info = {
                    "node_id": node_id_str,
                    "error": str(node_state.error) if node_state.error else "Unknown error",
                    "status": "failed",
                }
                already_added = any(e["node_id"] == node_id_str for e in execution_errors)
                if not already_added:
                    execution_errors.append(error_info)

    def _build_node_output(
        self,
        node: SubDiagramNode,
        execution_results: dict[str, Any],
        trace_id: str = "",
        execution_errors: list[dict[str, Any]] | None = None,
    ) -> Envelope:
        """Build and return an Envelope with execution results.

        Creates an Envelope containing the execution results and errors summary.
        """
        output_value = self._process_output_mapping(node, execution_results)

        envelope = EnvelopeFactory.create(
            body=output_value, produced_by=node.id, trace_id=trace_id, meta={}
        )

        metadata = {
            "execution_mode": "lightweight",
            "execution_status": "completed" if not execution_errors else "completed_with_errors",
            "diagram_name": node.diagram_name or "inline",
            "node_count": len(execution_results),
        }

        if execution_errors:
            metadata["errors"] = execution_errors
            metadata["error_count"] = len(execution_errors)

        return envelope.with_meta(**metadata)

    def _create_isolated_registry(self, parent_registry):
        """Create an isolated service registry for sub-diagram execution.

        Copies the parent registry to prevent state contamination between parallel executions.
        """
        from dipeo.application.registry import ServiceRegistry

        isolated_registry = ServiceRegistry()

        if hasattr(parent_registry, "_services"):
            for key_str, service in parent_registry._services.items():
                isolated_registry._services[key_str] = service

        # Ensure critical services for person_job are available
        if hasattr(parent_registry, "resolve"):
            from dipeo.application.registry import (
                EXECUTION_ORCHESTRATOR,
                FILESYSTEM_ADAPTER,
                LLM_SERVICE,
                PROMPT_BUILDER,
            )

            critical_services = [
                (FILESYSTEM_ADAPTER, "filesystem_adapter"),
                (LLM_SERVICE, "llm_service"),
                (EXECUTION_ORCHESTRATOR, "execution_orchestrator"),
                (PROMPT_BUILDER, "prompt_builder"),
            ]

            for service_key, key_str in critical_services:
                try:
                    service = parent_registry.resolve(service_key)
                    if service and key_str not in isolated_registry._services:
                        isolated_registry._services[key_str] = service
                except Exception:
                    pass

        return isolated_registry

    async def _register_diagram_persons(
        self, diagram: "ExecutableDiagram", service_registry
    ) -> None:
        """Register persons from the diagram in the conversation manager.

        Ensures persons defined in sub_diagram are available when person_job nodes execute.
        """
        from dipeo.application.execution.wiring import EXECUTION_ORCHESTRATOR
        from dipeo.application.registry import ServiceKey

        orchestrator = None

        try:
            orchestrator = service_registry.resolve(EXECUTION_ORCHESTRATOR)
        except (KeyError, AttributeError):
            orchestrator_key = ServiceKey("execution.orchestrator")
            with contextlib.suppress(Exception):
                orchestrator = service_registry.resolve(orchestrator_key)

        if not orchestrator:
            logger.debug("No execution orchestrator found, skipping person registration")
            return

        orchestrator.register_diagram_persons(diagram)

    def _create_error_envelope(
        self,
        node: SubDiagramNode,
        trace_id: str,
        error_message: str,
        error_type: str,
        execution_errors: list[dict[str, Any]] | None = None,
    ) -> Envelope:
        """Create a standardized error envelope for sub-diagram failures.

        Ensures consistent error reporting with proper metadata.
        """
        error_data = {
            "error": error_message,
            "error_type": error_type,
            "diagram_name": node.diagram_name or "inline",
            "node_id": str(node.id),
        }

        if execution_errors:
            error_data["execution_errors"] = execution_errors

        return EnvelopeFactory.create(
            body=error_data,
            produced_by=node.id,
            trace_id=trace_id,
            meta={
                "execution_mode": "lightweight",
                "execution_status": "failed",
                "error_type": error_type,
                "has_sub_errors": bool(execution_errors),
            },
        )
