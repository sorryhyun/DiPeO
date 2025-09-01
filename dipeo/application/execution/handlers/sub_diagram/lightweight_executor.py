"""Lightweight sub-diagram executor that runs without state persistence.

This executor treats sub-diagrams as running "inside" the parent node,
without creating separate execution contexts or state persistence.
"""

import copy
import json
import logging
import os
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated import ExecutionID, ExecutionState, NodeState, Status, TokenUsage
from dipeo.diagram_generated.generated_nodes import SubDiagramNode
from dipeo.infrastructure.execution.messaging import NullEventBus

from .base_executor import BaseSubDiagramExecutor
from .parallel_executor import ParallelExecutionManager
from dipeo.application.execution.use_cases import PersonManagementUseCase

if TYPE_CHECKING:
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram

logger = logging.getLogger(__name__)


class LightweightSubDiagramExecutor(BaseSubDiagramExecutor):
    """Executes sub-diagrams without state persistence, treating them as internal node operations."""
    
    def __init__(self):
        """Initialize executor."""
        super().__init__()
        # Parallel execution manager (shared across all lightweight executions)
        self._parallel_manager: Optional[ParallelExecutionManager] = None
        # Track if fail_fast is enabled
        self._fail_fast = os.getenv("DIPEO_FAIL_FAST", "false").lower() == "true"
        # Use case for person management
        self._person_management_use_case = PersonManagementUseCase()
    
    def set_services(self, prepare_use_case, diagram_service):
        """Set services for the executor to use."""
        super().set_services(
            prepare_use_case=prepare_use_case,
            diagram_service=diagram_service
        )
    
    async def execute(self, request: ExecutionRequest[SubDiagramNode]) -> Envelope:
        """Execute a sub-diagram in lightweight mode without state persistence.
        
        Returns an Envelope containing the execution results.
        """
        node = request.node
        trace_id = request.execution_id or ""
        
        # Mark that we're in a sub-diagram context for nested sub-diagrams
        request.metadata['is_sub_diagram'] = True
        request.metadata['parent_diagram'] = node.diagram_name or 'inline'
        
        try:
            # Load and compile the diagram
            executable_diagram = await self._prepare_diagram(node, request)
            
            # Create minimal in-memory execution state with isolated service registry
            execution_state = self._create_in_memory_state(
                diagram=executable_diagram,
                inputs=request.inputs or {}
            )
            
            # Run the engine without observers or state persistence
            execution_results, execution_errors = await self._run_lightweight_execution(
                diagram=executable_diagram,
                execution_state=execution_state,
                request=request
            )
            
            # Check for fail_fast mode
            if self._fail_fast and execution_errors:
                first_error = execution_errors[0]
                logger.error(
                    f"Fail-fast triggered in sub-diagram '{node.diagram_name}' "
                    f"(node: {node.id}): {first_error['error']}"
                )
                # Return error envelope with all error details
                return self._create_error_envelope(
                    node=node,
                    trace_id=trace_id,
                    error_message=first_error['error'],
                    error_type="SubDiagramFailFastError",
                    execution_errors=execution_errors
                )
            
            # Build and return output with envelope
            return self._build_node_output(
                node=node,
                execution_results=execution_results,
                trace_id=trace_id,
                execution_errors=execution_errors
            )
            
        except Exception as e:
            logger.error(f"Error in lightweight sub-diagram execution for node {node.id}: {e}", exc_info=True)
            # Return standardized error envelope
            return self._create_error_envelope(
                node=node,
                trace_id=trace_id,
                error_message=str(e),
                error_type=type(e).__name__
            )
    
    async def _prepare_diagram(self, node: SubDiagramNode, request: ExecutionRequest) -> "ExecutableDiagram":
        """Prepare the diagram for execution (load and compile)."""
        if self._prepare_use_case:
            # Use the prepare use case for loading and compilation
            diagram_input = await self._get_diagram_input(node)
            
            # Get the diagram path for source path tracking
            diagram_id = None
            if node.diagram_name:
                diagram_id = self._construct_diagram_path(node)
            
            return await self._prepare_use_case.prepare_for_execution(
                diagram=diagram_input,
                diagram_id=diagram_id,  # Pass the path for metadata tracking
                validate=False  # Skip validation for lightweight execution
            )
        else:
            # Fallback to old implementation if service not available
            logger.warning("PrepareDiagramForExecutionUseCase not found, using fallback implementation")
            diagram_data = await self._load_diagram_fallback(node)
            return await self._compile_diagram_fallback(diagram_data)
    
    async def _get_diagram_input(self, node: SubDiagramNode) -> Any:
        """Get the diagram input for preparation.
        
        Returns either diagram_data dict, a DomainDiagram, or a string ID/path.
        """
        # If diagram_data is provided directly, return it
        if node.diagram_data:
            return node.diagram_data
        
        # Otherwise, construct the diagram path/ID
        if not node.diagram_name:
            raise ValueError("No diagram specified for execution")
        
        # Construct file path
        file_path = self._construct_diagram_path(node)
        
        # Try to load using diagram service if available
        if self._diagram_service:
            try:
                # Load the diagram - this returns a DomainDiagram
                diagram = await self._diagram_service.load_from_file(file_path)
                return diagram
            except Exception as e:
                logger.error(f"Error loading diagram from '{file_path}': {e!s}")
                # Return the path and let prepare use case try to load it
                return file_path
        else:
            # Return the path and let the prepare use case handle loading
            return file_path
    
    async def _load_diagram_fallback(self, node: SubDiagramNode) -> Any:
        """Fallback diagram loading (old implementation)."""
        # If diagram_data is provided directly, use it
        if node.diagram_data:
            return node.diagram_data
        
        # Otherwise, load by name from storage
        if not node.diagram_name:
            raise ValueError("No diagram specified for execution")
        
        if not self._diagram_service:
            raise ValueError("Diagram service not available")
        
        # Construct file path
        file_path = self._construct_diagram_path(node)
        
        try:
            # Load the diagram - this returns a DomainDiagram
            diagram = await self._diagram_service.load_from_file(file_path)
            return diagram
        except Exception as e:
            logger.error(f"Error loading diagram from '{file_path}': {e!s}")
            raise ValueError(f"Failed to load diagram '{node.diagram_name}': {e!s}")
    
    
    async def _compile_diagram_fallback(self, diagram_data: Any) -> "ExecutableDiagram":
        """Fallback diagram compilation using adapter."""
        from dipeo.diagram_generated import DomainDiagram
        from dipeo.infrastructure.diagram.adapters import StandardCompilerAdapter
        
        # Check if already a DomainDiagram
        if isinstance(diagram_data, DomainDiagram):
            domain_diagram = diagram_data
        # Convert dict to domain diagram
        elif isinstance(diagram_data, dict):
            domain_diagram = DomainDiagram.model_validate(diagram_data)
        else:
            raise ValueError(f"Unsupported diagram type: {type(diagram_data)}")
        
        # Compile to executable using adapter
        compiler = StandardCompilerAdapter(use_interface_based=True)
        executable_diagram = compiler.compile(domain_diagram)
        
        return executable_diagram
    
    def _create_in_memory_state(
        self, 
        diagram: "ExecutableDiagram",
        inputs: dict[str, Any]
    ) -> ExecutionState:
        """Create a minimal in-memory execution state."""
        # Create node states for all nodes
        node_states = {}
        for node in diagram.nodes:
            node_state = NodeState(
                status=Status.PENDING,
                started_at=None,
                ended_at=None,
                output=None,
                error=None,
                token_usage=None
            )
            node_states[str(node.id)] = node_state
        
        # Create execution state with proper variable handling
        # Ensure variables is either None or a proper dict that matches the expected schema
        variables = None
        if inputs:
            # If inputs has a 'default' key with nested dict, flatten it
            if 'default' in inputs and isinstance(inputs['default'], dict):
                # Use the nested dict directly as variables
                variables = inputs['default']
            elif inputs:
                # Use inputs as-is if it's already a proper dict
                variables = inputs
        
        execution_state = ExecutionState(
            id=ExecutionID(f"lightweight_{uuid.uuid4().hex[:8]}"),
            diagram_id=diagram.id if hasattr(diagram, 'id') else "unknown",
            status=Status.PENDING,
            started_at=datetime.now(UTC).isoformat(),
            node_states=node_states,
            node_outputs={},  # Initialize empty
            token_usage=TokenUsage(input=0, output=0, total=0),
            exec_counts={},  # Initialize empty
            executed_nodes=[],  # Initialize empty
            variables=variables  # Use the properly formatted variables
        )
        
        return execution_state
    
    async def _run_lightweight_execution(
        self,
        diagram: "ExecutableDiagram",
        execution_state: ExecutionState,
        request: ExecutionRequest
    ) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Run the execution engine without observers or state persistence.
        
        Returns:
            Tuple of (execution_results, execution_errors)
        """
        from dipeo.application.execution.typed_engine import TypedExecutionEngine
        from dipeo.application.registry import ServiceRegistry
        from dipeo.domain.execution.resolution import resolve_inputs
        from dipeo.domain.execution.envelope import Envelope
        
        # Create a minimal runtime resolver that directly uses domain resolution
        class MinimalResolver:
            def resolve_node_inputs(self, node, incoming_edges, context):
                """Resolve inputs using domain resolution directly."""
                from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
                
                # Create minimal diagram for resolution
                diagram = ExecutableDiagram(
                    id="temp",
                    nodes=[node],
                    edges=incoming_edges,
                    metadata={}
                )
                
                # Use domain resolution (synchronous)
                envelopes = resolve_inputs(node, diagram, context)
                
                # Extract raw values from envelopes
                return {key: env.body for key, env in envelopes.items()}
            
            async def resolve_as_envelopes(self, node, context, diagram):
                """Resolve as envelopes - just wraps synchronous call."""
                return resolve_inputs(node, diagram, context)
        
        runtime_resolver = MinimalResolver()
        
        # Create isolated service registry (copy from parent but independent)
        parent_registry = request.parent_registry or request.services
        isolated_registry = self._create_isolated_registry(parent_registry)
        
        # Register persons from the diagram in the orchestrator/conversation manager
        await self._register_diagram_persons(diagram, isolated_registry)
        
        # Create engine with null event bus (no events emitted)
        engine = TypedExecutionEngine(
            service_registry=isolated_registry,
            runtime_resolver=runtime_resolver,
            event_bus=NullEventBus()  # No event emission
        )
        
        # Run execution and collect outputs and errors
        execution_results = {}
        execution_errors = []
        
        async for update in engine.execute(
            diagram=diagram,
            execution_state=execution_state,
            options={
                "is_lightweight": True,
                "parent_node_id": str(request.node.id),
                "parent_metadata": request.metadata  # Pass parent metadata to nested executions
            },
            container=request.parent_container,
            interactive_handler=None
        ):
            # Process updates and collect outputs
            self._process_execution_update(update, execution_state, execution_results, execution_errors)
            
            # Check for fail_fast
            if self._fail_fast and execution_errors:
                logger.warning(f"Fail-fast triggered, stopping execution of sub-diagram")
                break
        
        # Collect any remaining outputs after execution completes
        self._collect_final_outputs(execution_state, execution_results, execution_errors)
        
        return execution_results, execution_errors
    
    def _process_execution_update(
        self,
        update: dict[str, Any],
        execution_state: ExecutionState,
        execution_results: dict[str, Any],
        execution_errors: list[dict[str, Any]]
    ) -> None:
        """Process execution updates and collect completed outputs and errors.
        
        Handles both envelope-based and legacy outputs from nodes.
        """
        if update.get("type") == "step_complete":
            # After each step, check for completed nodes and collect outputs
            for node_id_str, node_state in execution_state.node_states.items():
                if node_state.status == Status.COMPLETED and node_state.output:
                    if node_id_str not in execution_results:
                        # Extract value from Envelope if present
                        output = node_state.output
                        if hasattr(output, 'value'):
                            execution_results[node_id_str] = output.value
                        else:
                            execution_results[node_id_str] = output
                elif node_state.status == Status.FAILED:
                    # Track failed nodes
                    error_info = {
                        "node_id": node_id_str,
                        "error": str(node_state.error) if node_state.error else "Unknown error",
                        "status": "failed"
                    }
                    if error_info not in execution_errors:
                        execution_errors.append(error_info)
    
    def _collect_final_outputs(
        self,
        execution_state: ExecutionState,
        execution_results: dict[str, Any],
        execution_errors: list[dict[str, Any]]
    ) -> None:
        """Collect any remaining outputs and errors after execution completes.
        
        Handles both envelope-based and legacy outputs from nodes.
        """
        for node_id_str, node_state in execution_state.node_states.items():
            if node_state.status == Status.COMPLETED and node_state.output:
                if node_id_str not in execution_results:
                    # Extract value from Envelope if present
                    output = node_state.output
                    if hasattr(output, 'value'):
                        execution_results[node_id_str] = output.value
                    else:
                        execution_results[node_id_str] = output
            elif node_state.status == Status.FAILED:
                # Track failed nodes
                error_info = {
                    "node_id": node_id_str,
                    "error": str(node_state.error) if node_state.error else "Unknown error",
                    "status": "failed"
                }
                # Check if not already added
                already_added = any(
                    e["node_id"] == node_id_str for e in execution_errors
                )
                if not already_added:
                    execution_errors.append(error_info)
    
    def _build_node_output(
        self,
        node: SubDiagramNode,
        execution_results: dict[str, Any],
        trace_id: str = "",
        execution_errors: Optional[list[dict[str, Any]]] = None
    ) -> Envelope:
        """Build and return an Envelope with execution results.
        
        Creates an Envelope containing the execution results and errors summary.
        """
        # Process output mapping
        output_value = self._process_output_mapping(node, execution_results)
        
        # Determine envelope type and create it directly
        if isinstance(output_value, dict):
            envelope = EnvelopeFactory.json(
                output_value,
                produced_by=node.id,
                trace_id=trace_id
            )
        elif isinstance(output_value, str):
            envelope = EnvelopeFactory.text(
                output_value,
                produced_by=node.id,
                trace_id=trace_id
            )
        else:
            # Default to JSON for complex types
            envelope = EnvelopeFactory.json(
                output_value if isinstance(output_value, (dict, list)) else {"value": output_value},
                produced_by=node.id,
                trace_id=trace_id
            )
        
        # Build metadata including error summary
        metadata = {
            "execution_mode": "lightweight",
            "execution_status": "completed" if not execution_errors else "completed_with_errors",
            "diagram_name": node.diagram_name or "inline",
            "node_count": len(execution_results)
        }
        
        # Include error summary if there were errors
        if execution_errors:
            metadata["errors"] = execution_errors
            metadata["error_count"] = len(execution_errors)
        
        # Add execution metadata to envelope
        return envelope.with_meta(**metadata)
    
    def _create_isolated_registry(self, parent_registry):
        """Create an isolated service registry for sub-diagram execution.
        
        This creates a copy of the parent registry to prevent state contamination
        between parallel sub-diagram executions.
        """
        from dipeo.application.registry import ServiceRegistry
        
        # Create new registry instance
        isolated_registry = ServiceRegistry()
        
        # Copy services from parent registry if possible
        if hasattr(parent_registry, '_services'):
            # Deep copy the services to ensure isolation
            # The registry stores keys as strings internally
            for key_str, service in parent_registry._services.items():
                # Directly assign to internal dict since keys are already strings
                isolated_registry._services[key_str] = service
        
        # Also try to copy services using the resolve method for compatibility
        # This ensures we get all services even if they're stored differently
        if hasattr(parent_registry, 'resolve'):
            from dipeo.application.registry import (
                FILESYSTEM_ADAPTER,
                LLM_SERVICE,
                EXECUTION_ORCHESTRATOR,
                PROMPT_BUILDER,
            )
            
            # Critical services that person_job needs
            critical_services = [
                (FILESYSTEM_ADAPTER, 'filesystem_adapter'),
                (LLM_SERVICE, 'llm_service'),
                (EXECUTION_ORCHESTRATOR, 'execution_orchestrator'),
                (PROMPT_BUILDER, 'prompt_builder'),
            ]
            
            for service_key, key_str in critical_services:
                try:
                    service = parent_registry.resolve(service_key)
                    if service and key_str not in isolated_registry._services:
                        isolated_registry._services[key_str] = service
                except:
                    # Service might not be available, continue
                    pass
        
        return isolated_registry
    
    async def _register_diagram_persons(self, diagram: "ExecutableDiagram", service_registry) -> None:
        """Register persons from the diagram in the conversation manager.
        
        This ensures that persons defined in the sub_diagram are available
        when person_job nodes try to get or create them.
        """
        # Get the orchestrator from the service registry
        from dipeo.application.registry import ServiceKey
        from dipeo.application.execution.wiring import EXECUTION_ORCHESTRATOR
        
        orchestrator = None
        
        try:
            orchestrator = service_registry.resolve(EXECUTION_ORCHESTRATOR)
        except (KeyError, AttributeError):
            # Try alternative key with correct string
            orchestrator_key = ServiceKey("execution.orchestrator")
            try:
                orchestrator = service_registry.resolve(orchestrator_key)
            except:
                pass
        
        if not orchestrator:
            logger.debug("No execution orchestrator found, skipping person registration")
            return
        
        # Use the person management use case to register all persons
        self._person_management_use_case.register_diagram_persons(
            diagram,
            orchestrator
        )
    
    def _create_error_envelope(
        self,
        node: SubDiagramNode,
        trace_id: str,
        error_message: str,
        error_type: str,
        execution_errors: Optional[list[dict[str, Any]]] = None
    ) -> Envelope:
        """Create a standardized error envelope for sub-diagram failures.
        
        This ensures consistent error reporting with proper metadata.
        """
        error_data = {
            "error": error_message,
            "error_type": error_type,
            "diagram_name": node.diagram_name or "inline",
            "node_id": str(node.id)
        }
        
        # Include detailed execution errors if available
        if execution_errors:
            error_data["execution_errors"] = execution_errors
        
        # Create error envelope
        return EnvelopeFactory.json(
            error_data,
            produced_by=node.id,
            trace_id=trace_id
        ).with_meta(
            execution_mode="lightweight",
            execution_status="failed",
            error_type=error_type,
            has_sub_errors=bool(execution_errors)
        )
    
