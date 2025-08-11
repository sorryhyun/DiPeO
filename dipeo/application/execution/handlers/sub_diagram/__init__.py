"""Handler for SubDiagramNode - executes diagrams within diagrams.

This modular structure follows the pattern of condition and code_job handlers:
- __init__.py - Main handler with routing logic
- single_executor.py - Single sub-diagram execution  
- batch_executor.py - Optimized parallel batch execution
"""

from typing import TYPE_CHECKING, Optional
import logging

from pydantic import BaseModel

from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.execution.handler_factory import register_handler
from dipeo.diagram_generated.generated_nodes import SubDiagramNode, NodeType
from dipeo.core.execution.node_output import NodeOutputProtocol
from dipeo.diagram_generated.models.sub_diagram_model import SubDiagramNodeData

from .single_executor import SingleSubDiagramExecutor
from .batch_executor import BatchSubDiagramExecutor
from .lightweight_executor import LightweightSubDiagramExecutor

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)


@register_handler
class SubDiagramNodeHandler(TypedNodeHandler[SubDiagramNode]):
    """Handler for executing diagrams within diagrams.
    
    This handler allows a diagram to execute another diagram as a node,
    passing inputs and receiving outputs from the sub-diagram execution.
    Routes execution to appropriate executor based on batch configuration.
    
    Sub-diagrams run in lightweight mode by default - they execute "inside" the
    parent node without creating separate execution states or persistence.
    """
    
    def __init__(self):
        """Initialize with lightweight, single and batch executors."""
        self.lightweight_executor = LightweightSubDiagramExecutor()
        self.single_executor = SingleSubDiagramExecutor()  # Keep for backward compatibility
        self.batch_executor = BatchSubDiagramExecutor()
    
    @property
    def requires_services(self) -> list[str]:
        return ["state_store", "message_router", "diagram_service"]
    
    @property
    def node_class(self) -> type[SubDiagramNode]:
        return SubDiagramNode
    
    @property
    def node_type(self) -> str:
        return NodeType.SUB_DIAGRAM.value
    
    @property
    def schema(self) -> type[BaseModel]:
        return SubDiagramNodeData
    
    @property
    def description(self) -> str:
        return "Execute another diagram as a node within the current diagram"
    
    def validate(self, request: ExecutionRequest[SubDiagramNode]) -> Optional[str]:
        """Validate the sub-diagram node configuration."""
        node = request.node
        
        # Validate that either diagram_name or diagram_data is provided
        if not node.diagram_name and not node.diagram_data:
            return "Either diagram_name or diagram_data must be specified"
        
        # If both are provided, warn but continue
        if node.diagram_name and node.diagram_data:
            log.warning(f"Both diagram_name and diagram_data provided for node {node.id}. diagram_data will be used.")
        
        return None
    
    async def execute_request(self, request: ExecutionRequest[SubDiagramNode]) -> NodeOutputProtocol:
        """Route execution to appropriate executor based on configuration."""
        node = request.node
        
        # Check if batch mode is enabled
        if getattr(node, 'batch', False) and getattr(node, 'batch_parallel', False):
            # Use optimized batch executor for parallel execution
            return await self.batch_executor.execute(request)
        elif getattr(node, 'batch', False):
            # Use batch executor in sequential mode
            return await self.batch_executor.execute(request)
        else:
            # Use lightweight executor for normal execution
            # Sub-diagrams run "inside" the parent node without separate state
            return await self.lightweight_executor.execute(request)
    
    def post_execute(
        self,
        request: ExecutionRequest[SubDiagramNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        """Post-execution hook to log sub-diagram execution."""
        # Log execution details if in debug mode
        if request.metadata and request.metadata.get("debug"):
            sub_execution_id = request.metadata.get("sub_execution_id", "unknown")
            log.debug(f"Sub-diagram execution completed: {sub_execution_id}")
        
        return output