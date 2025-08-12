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
from dipeo.core.execution.node_output import NodeOutputProtocol, ErrorOutput
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
    
    Clean separation of concerns:
    1. validate() - Static/structural validation (compile-time checks)
    2. pre_execute() - Runtime validation and setup
    3. execute_request() - Core execution logic
    
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
        # Instance variables for passing data between methods
        self._current_executor_type = None
        self._current_executor = None
    
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
    
    async def pre_execute(self, request: ExecutionRequest[SubDiagramNode]) -> Optional[NodeOutputProtocol]:
        """Pre-execution setup: validate services and determine executor.
        
        Moves batch mode detection and executor selection out of execute_request
        for cleaner separation of concerns.
        """
        node = request.node
        
        # Validate required services are available
        if not request.services:
            return ErrorOutput(
                value="Required services not available for sub-diagram execution",
                node_id=node.id,
                error_type="ServiceNotAvailableError"
            )
        
        # Check for required services
        required = ["state_store", "message_router", "diagram_service"]
        missing = [svc for svc in required if svc not in request.services]
        if missing:
            return ErrorOutput(
                value=f"Missing required services: {', '.join(missing)}",
                node_id=node.id,
                error_type="ServiceNotAvailableError"
            )
        
        # Determine which executor to use based on batch configuration
        # Store in instance variables for execute_request to use
        if getattr(node, 'batch', False):
            if getattr(node, 'batch_parallel', False):
                self._current_executor_type = 'batch_parallel'
                self._current_executor = self.batch_executor
            else:
                self._current_executor_type = 'batch_sequential'
                self._current_executor = self.batch_executor
        else:
            self._current_executor_type = 'lightweight'
            self._current_executor = self.lightweight_executor
        
        # No early return - proceed to execute_request
        return None
    
    async def execute_request(self, request: ExecutionRequest[SubDiagramNode]) -> NodeOutputProtocol:
        """Pure execution using instance variables set in pre_execute.
        
        Simplified logic - executor already determined in pre_execute.
        """
        # Use executor from instance variable (set in pre_execute)
        executor = self._current_executor or self.lightweight_executor
        
        # Execute using the selected executor
        return await executor.execute(request)
    
    def post_execute(
        self,
        request: ExecutionRequest[SubDiagramNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        """Post-execution hook to log sub-diagram execution."""
        # Post-execution logging can use instance variables if needed
        # No need for metadata access
        return output