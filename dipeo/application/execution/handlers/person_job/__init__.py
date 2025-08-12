"""Handler for PersonJobNode - executes AI person jobs with conversation memory.

This modular structure follows the pattern of condition and code_job handlers:
- __init__.py - Main handler with routing logic
- single_executor.py - Single person execution logic
- batch_executor.py - Optimized parallel batch execution
"""

import logging
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.handler_base import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.domain.conversation import Person
from dipeo.diagram_generated.generated_nodes import PersonJobNode, NodeType
from dipeo.core.execution.node_output import NodeOutputProtocol, ErrorOutput
from dipeo.diagram_generated.models.person_job_model import PersonJobNodeData

from .single_executor import SinglePersonJobExecutor
from .batch_executor import BatchPersonJobExecutor

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@register_handler
class PersonJobNodeHandler(TypedNodeHandler[PersonJobNode]):
    """Handler for executing AI person jobs with conversation memory.
    
    This handler supports both single person execution and batch execution
    for processing multiple items through the same person configuration.
    Routes execution to appropriate executor based on batch configuration.
    """
    
    def __init__(self):
        # Person cache managed at handler level and shared between executors
        self._person_cache: dict[str, Person] = {}
        
        # Initialize executors
        self.single_executor = SinglePersonJobExecutor(self._person_cache)
        self.batch_executor = BatchPersonJobExecutor(self._person_cache)
        
        # Instance variable for debug flag
        self._current_debug = False
        
        # Services for executors (will be set in pre_execute)
        self._services_configured = False

    @property
    def node_class(self) -> type[PersonJobNode]:
        return PersonJobNode
    
    @property
    def node_type(self) -> str:
        return NodeType.PERSON_JOB.value

    @property
    def schema(self) -> type[BaseModel]:
        return PersonJobNodeData

    @property
    def requires_services(self) -> list[str]:
        return [
            "llm_service", 
            "diagram", 
            "conversation_manager",
            "prompt_builder",
            "filesystem_adapter",
        ]

    @property
    def description(self) -> str:
        return "Execute person job with conversation memory, supporting both single and batch execution"
    
    def validate(self, request: ExecutionRequest[PersonJobNode]) -> Optional[str]:
        """Validate the execution request."""
        node = request.node
        
        if not node.person:
            return "No person specified"
        
        # Validate batch configuration
        if getattr(node, 'batch', False):
            batch_input_key = getattr(node, 'batch_input_key', 'items')
            if not batch_input_key:
                return "Batch mode enabled but batch_input_key not specified"
        
        return None
    
    async def pre_execute(self, request: ExecutionRequest[PersonJobNode]) -> Optional[NodeOutputProtocol]:
        """Pre-execution hook to check max_iteration limit and configure services."""
        node = request.node
        context = request.context
        
        # Set debug flag for later use (could be from context or environment)
        self._current_debug = False  # Will be set based on context if needed
        
        # Configure services for executors on first execution
        if not self._services_configured:
            from dipeo.application.registry import (
                LLM_SERVICE,
                DIAGRAM,
                CONVERSATION_MANAGER,
                PROMPT_BUILDER,
                FILESYSTEM_ADAPTER
            )
            
            llm_service = request.services.resolve(LLM_SERVICE)
            diagram = request.services.resolve(DIAGRAM)
            conversation_manager = request.services.resolve(CONVERSATION_MANAGER)
            prompt_builder = request.services.resolve(PROMPT_BUILDER)
            filesystem_adapter = request.services.resolve(FILESYSTEM_ADAPTER)
            
            # Set services on executors
            self.single_executor.set_services(
                llm_service=llm_service,
                diagram=diagram,
                conversation_manager=conversation_manager,
                prompt_builder=prompt_builder,
                filesystem_adapter=filesystem_adapter
            )
            
            # BatchExecutor uses SingleExecutor internally, so it inherits the services
            self._services_configured = True
        
        # Max iteration check is now handled in the engine before transition_node_to_running
        # Just log for debugging
        execution_count = context.get_node_execution_count(node.id)
        logger.info(f"[PRE_EXECUTE] PersonJobNode {node.id} - execution_count: {execution_count}, max_iteration: {node.max_iteration}")
        
        # Return None to proceed with normal execution
        return None
    
    async def execute_request(self, request: ExecutionRequest[PersonJobNode]) -> NodeOutputProtocol:
        """Route execution to appropriate executor based on configuration."""
        node = request.node
        
        try:
            # Check if batch mode is enabled
            if getattr(node, 'batch', False):
                logger.info(f"Executing PersonJobNode {node.id} in batch mode")
                # Use batch executor for batch execution
                return await self.batch_executor.execute(request)
            else:
                # Use single executor for normal execution
                return await self.single_executor.execute(request)
        except Exception as e:
            # Let on_error handle it
            raise
    
    async def on_error(
        self,
        request: ExecutionRequest[PersonJobNode],
        error: Exception
    ) -> Optional[NodeOutputProtocol]:
        """Handle errors gracefully."""
        # For ValueError (domain validation), only log in debug mode
        if isinstance(error, ValueError):
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Validation error in person job: {error}")
            return ErrorOutput(
                value=str(error),
                node_id=request.node.id,
                error_type="ValidationError"
            )
        
        # For other errors, log them
        logger.error(f"Error executing person job: {error}")
        return ErrorOutput(
            value=str(error),
            node_id=request.node.id,
            error_type=type(error).__name__
        )
    
    def post_execute(
        self,
        request: ExecutionRequest[PersonJobNode],
        output: NodeOutputProtocol
    ) -> NodeOutputProtocol:
        """Post-execution hook to log execution details."""
        # Log execution details if in debug mode (using instance variable)
        if self._current_debug:
            is_batch = getattr(request.node, 'batch', False)
            if is_batch:
                batch_info = output.value if hasattr(output, 'value') else {}
                total = batch_info.get('total_items', 0)
                successful = batch_info.get('successful', 0)
                logger.debug(f"Batch person job completed: {successful}/{total} successful")
            else:
                logger.debug(f"Person job completed for {request.node.person}")
        
        return output