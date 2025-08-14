"""Lightweight sub-diagram executor that runs without state persistence.

This executor treats sub-diagrams as running "inside" the parent node,
without creating separate execution contexts or state persistence.
"""

import json
import logging
import uuid
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated import ExecutionID, ExecutionState, NodeState, Status, TokenUsage
from dipeo.diagram_generated.generated_nodes import SubDiagramNode
from dipeo.infrastructure.events import NullEventBus

from .base_executor import BaseSubDiagramExecutor

if TYPE_CHECKING:
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram

logger = logging.getLogger(__name__)


class LightweightSubDiagramExecutor(BaseSubDiagramExecutor):
    """Executes sub-diagrams without state persistence, treating them as internal node operations."""
    
    def __init__(self):
        """Initialize executor."""
        super().__init__()
    
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
        
        try:
            # Load and compile the diagram
            executable_diagram = await self._prepare_diagram(node, request)
            
            # Create minimal in-memory execution state
            execution_state = self._create_in_memory_state(
                diagram=executable_diagram,
                inputs=request.inputs or {}
            )
            
            # Run the engine without observers or state persistence
            execution_results = await self._run_lightweight_execution(
                diagram=executable_diagram,
                execution_state=execution_state,
                request=request
            )
            
            # Build and return output with envelope
            return self._build_node_output(
                node=node,
                execution_results=execution_results,
                trace_id=trace_id
            )
            
        except Exception as e:
            logger.error(f"Error in lightweight sub-diagram execution for node {node.id}: {e}", exc_info=True)
            error_data = {"error": str(e)}
            # Return error envelope directly
            return EnvelopeFactory.json(
                error_data,
                produced_by=node.id,
                trace_id=trace_id
            ).with_meta(
                execution_mode="lightweight",
                execution_status="failed",
                error_type=type(e).__name__
            )
    
    async def _prepare_diagram(self, node: SubDiagramNode, request: ExecutionRequest) -> "ExecutableDiagram":
        """Prepare the diagram for execution (load and compile)."""
        if self._prepare_use_case:
            # Use the prepare use case for loading and compilation
            diagram_input = await self._get_diagram_input(node)
            return await self._prepare_use_case.prepare_for_execution(
                diagram=diagram_input,
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
        """Fallback diagram compilation (old implementation)."""
        from dipeo.diagram_generated import DomainDiagram
        from dipeo.infrastructure.services.diagram.compilation_service import CompilationService
        
        # Check if already a DomainDiagram
        if isinstance(diagram_data, DomainDiagram):
            domain_diagram = diagram_data
        # Convert dict to domain diagram
        elif isinstance(diagram_data, dict):
            domain_diagram = DomainDiagram.model_validate(diagram_data)
        else:
            raise ValueError(f"Unsupported diagram type: {type(diagram_data)}")
        
        # Compile to executable
        compiler = CompilationService()
        await compiler.initialize()
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
    ) -> dict[str, Any]:
        """Run the execution engine without observers or state persistence."""
        from dipeo.application.execution.resolvers import StandardRuntimeResolver
        from dipeo.application.execution.typed_engine import TypedExecutionEngine
        
        # Create a minimal runtime resolver
        runtime_resolver = StandardRuntimeResolver()
        
        # Create engine with null event bus (no events emitted)
        engine = TypedExecutionEngine(
            service_registry=request.parent_registry or request.services,
            runtime_resolver=runtime_resolver,
            event_bus=NullEventBus(),  # No event emission
            observers=None  # No observers
        )
        
        # Run execution and collect outputs
        execution_results = {}
        
        async for update in engine.execute(
            diagram=diagram,
            execution_state=execution_state,
            options={
                "is_lightweight": True,
                "parent_node_id": str(request.node.id)
            },
            container=request.parent_container,
            interactive_handler=None
        ):
            # Process updates and collect outputs
            self._process_execution_update(update, execution_state, execution_results)
        
        # Collect any remaining outputs after execution completes
        self._collect_final_outputs(execution_state, execution_results)
        
        return execution_results
    
    def _process_execution_update(
        self,
        update: dict[str, Any],
        execution_state: ExecutionState,
        execution_results: dict[str, Any]
    ) -> None:
        """Process execution updates and collect completed outputs.
        
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
    
    def _collect_final_outputs(
        self,
        execution_state: ExecutionState,
        execution_results: dict[str, Any]
    ) -> None:
        """Collect any remaining outputs after execution completes.
        
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
    
    def _build_node_output(
        self,
        node: SubDiagramNode,
        execution_results: dict[str, Any],
        trace_id: str = ""
    ) -> Envelope:
        """Build and return an Envelope with execution results.
        
        Creates an Envelope containing the execution results.
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
        
        # Add execution metadata to envelope
        return envelope.with_meta(
            execution_mode="lightweight",
            execution_status="completed",
            diagram_name=node.diagram_name or "inline",
            node_count=len(execution_results)
        )
    
