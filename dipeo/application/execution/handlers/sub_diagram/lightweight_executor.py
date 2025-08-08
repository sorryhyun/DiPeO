"""Lightweight sub-diagram executor that runs without state persistence.

This executor treats sub-diagrams as running "inside" the parent node,
without creating separate execution contexts or state persistence.
"""

from typing import TYPE_CHECKING, Any, Optional
import logging
import uuid
from datetime import datetime, UTC

from dipeo.core.execution.node_output import DataOutput, NodeOutputProtocol
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.diagram_generated.generated_nodes import SubDiagramNode
from dipeo.diagram_generated import ExecutionState, Status, NodeState, NodeID, DomainDiagram, TokenUsage, ExecutionID
from dipeo.infrastructure.events import NullEventBus
from dipeo.application.registry.keys import PREPARE_DIAGRAM_USE_CASE

if TYPE_CHECKING:
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
    from dipeo.application.execution.use_cases import PrepareDiagramForExecutionUseCase

log = logging.getLogger(__name__)


class LightweightSubDiagramExecutor:
    """Executes sub-diagrams without state persistence, treating them as internal node operations."""
    
    async def execute(self, request: ExecutionRequest[SubDiagramNode]) -> NodeOutputProtocol:
        """Execute a sub-diagram in lightweight mode without state persistence."""
        node = request.node
        
        try:
            # Get the prepare diagram use case from the registry
            prepare_use_case = request.services.resolve(PREPARE_DIAGRAM_USE_CASE)
            if not prepare_use_case:
                # Fallback to old implementation if service not available
                log.warning("PrepareDiagramForExecutionUseCase not found, using fallback implementation")
                diagram_data = await self._load_diagram_fallback(node, request)
                executable_diagram = await self._compile_diagram_fallback(diagram_data)
            else:
                # Use the prepare use case for loading and compilation
                diagram_input = await self._get_diagram_input(node, request)
                executable_diagram = await prepare_use_case.prepare_for_execution(
                    diagram=diagram_input,
                    validate=False  # Skip validation for lightweight execution
                )
            
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
            
            # Process output mapping
            output_value = self._process_output_mapping(node, execution_results)
            
            # Return output
            return DataOutput(
                value=output_value,
                node_id=node.id,
                metadata={
                    "execution_mode": "lightweight",
                    "status": "completed"
                }
            )
            
        except Exception as e:
            log.error(f"Error in lightweight sub-diagram execution for node {node.id}: {e}", exc_info=True)
            return DataOutput(
                value={"error": str(e)},
                node_id=node.id,
                metadata={
                    "execution_mode": "lightweight",
                    "status": "error",
                    "error": str(e)
                }
            )
    
    async def _get_diagram_input(self, node: SubDiagramNode, request: ExecutionRequest) -> Any:
        """Get the diagram input for preparation.
        
        Returns either diagram_data dict, a DomainDiagram, or a string ID/path.
        """
        # If diagram_data is provided directly, return it
        if node.diagram_data:
            return node.diagram_data
        
        # Otherwise, construct the diagram path/ID
        if not node.diagram_name:
            raise ValueError("No diagram specified for execution")
        
        diagram_name = node.diagram_name
        format_suffix = ".light.yaml"  # Default format
        
        if node.diagram_format:
            format_map = {
                'light': '.light.yaml',
                'native': '.native.json',
                'readable': '.readable.yaml'
            }
            format_suffix = format_map.get(node.diagram_format, '.light.yaml')
        
        # Construct full file path
        if diagram_name.startswith('codegen/'):
            file_path = f"files/{diagram_name}{format_suffix}"
        else:
            file_path = f"files/diagrams/{diagram_name}{format_suffix}"
        
        # Load the diagram using the diagram service
        from dipeo.application.registry.keys import DIAGRAM_SERVICE_NEW
        diagram_service = request.services.resolve(DIAGRAM_SERVICE_NEW)
        
        if not diagram_service:
            # Return the path and let the prepare use case handle loading
            return file_path
        
        try:
            # Load the diagram - this returns a DomainDiagram
            diagram = await diagram_service.load_from_file(file_path)
            return diagram
        except Exception as e:
            log.error(f"Error loading diagram from '{file_path}': {str(e)}")
            # Return the path and let prepare use case try to load it
            return file_path
    
    async def _load_diagram_fallback(self, node: SubDiagramNode, request: ExecutionRequest) -> Any:
        """Fallback diagram loading (old implementation)."""
        # If diagram_data is provided directly, use it
        if node.diagram_data:
            return node.diagram_data
        
        # Otherwise, load by name from storage
        if not node.diagram_name:
            raise ValueError("No diagram specified for execution")
        
        from dipeo.application.registry.keys import DIAGRAM_SERVICE_NEW
        diagram_service = request.services.resolve(DIAGRAM_SERVICE_NEW)
        
        if not diagram_service:
            raise ValueError("Diagram service not available")
        
        # Construct file path based on diagram name and format
        diagram_name = node.diagram_name
        format_suffix = ".light.yaml"  # Default format
        
        if node.diagram_format:
            format_map = {
                'light': '.light.yaml',
                'native': '.native.json',
                'readable': '.readable.yaml'
            }
            format_suffix = format_map.get(node.diagram_format, '.light.yaml')
        
        # Construct full file path
        if diagram_name.startswith('codegen/'):
            file_path = f"files/{diagram_name}{format_suffix}"
        else:
            file_path = f"files/diagrams/{diagram_name}{format_suffix}"
        
        try:
            # Load the diagram - this returns a DomainDiagram
            diagram = await diagram_service.load_from_file(file_path)
            return diagram
        except Exception as e:
            log.error(f"Error loading diagram from '{file_path}': {str(e)}")
            raise ValueError(f"Failed to load diagram '{node.diagram_name}': {str(e)}")
    
    async def _compile_diagram_fallback(self, diagram_data: Any) -> "ExecutableDiagram":
        """Fallback diagram compilation (old implementation)."""
        from dipeo.diagram_generated import DomainDiagram
        from dipeo.domain.diagram.utils import dict_to_domain_diagram
        from dipeo.infrastructure.services.diagram.compilation_service import CompilationService
        
        # Check if already a DomainDiagram
        if isinstance(diagram_data, DomainDiagram):
            domain_diagram = diagram_data
        # Convert dict to domain diagram
        elif isinstance(diagram_data, dict):
            domain_diagram = dict_to_domain_diagram(diagram_data)
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
        
        # Create execution state
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
            variables=inputs
        )
        
        return execution_state
    
    async def _run_lightweight_execution(
        self,
        diagram: "ExecutableDiagram",
        execution_state: ExecutionState,
        request: ExecutionRequest
    ) -> dict[str, Any]:
        """Run the execution engine without observers or state persistence."""
        from dipeo.application.execution.typed_engine import TypedExecutionEngine
        from dipeo.application.execution.resolvers import StandardRuntimeResolver
        
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
            # The engine yields step results
            if update.get("type") == "step_complete":
                # After each step, check for completed nodes and collect outputs
                for node_id_str, node_state in execution_state.node_states.items():
                    if node_state.status == Status.COMPLETED and node_state.output:
                        if node_id_str not in execution_results:
                            execution_results[node_id_str] = node_state.output
        
        # Also collect any remaining outputs after execution completes
        for node_id_str, node_state in execution_state.node_states.items():
            if node_state.status == Status.COMPLETED and node_state.output:
                if node_id_str not in execution_results:
                    execution_results[node_id_str] = node_state.output
        
        return execution_results
    
    def _process_output_mapping(self, node: SubDiagramNode, execution_results: dict[str, Any]) -> dict[str, Any]:
        """Process output mapping from sub-diagram results."""
        if not execution_results:
            return {}
        
        # Find endpoint outputs
        endpoint_outputs = {
            k: v for k, v in execution_results.items() 
            if k.startswith("endpoint") or k.startswith("end")
        }
        
        if endpoint_outputs:
            # If there's one endpoint, return its value directly
            if len(endpoint_outputs) == 1:
                return list(endpoint_outputs.values())[0]
            # Multiple endpoints, return all
            return endpoint_outputs
        
        # No endpoints, return the last output
        return list(execution_results.values())[-1] if execution_results else {}