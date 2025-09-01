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
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
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
    
    Now uses envelope-based communication for clean input/output interfaces.
    """
    
    NODE_TYPE = NodeType.PERSON_JOB.value
    
    def __init__(self):
        super().__init__()
        
        # Initialize executors (no longer passing person cache - will use orchestrator)
        self.single_executor = SinglePersonJobExecutor()
        self.batch_executor = BatchPersonJobExecutor()
        
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
            "execution_orchestrator",
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
    
    async def pre_execute(self, request: ExecutionRequest[PersonJobNode]) -> Optional[Envelope]:
        """Pre-execution hook to check max_iteration limit and configure services."""
        node = request.node
        context = request.context
        
        # Set debug flag for later use (could be from context or environment)
        self._current_debug = False  # Will be set based on context if needed
        
        # Configure services for executors on first execution
        if not self._services_configured:
            from dipeo.application.registry.keys import (
                LLM_SERVICE,
                DIAGRAM,
                EXECUTION_ORCHESTRATOR,
                PROMPT_BUILDER,
                FILESYSTEM_ADAPTER
            )
            
            llm_service = request.services.resolve(LLM_SERVICE)
            diagram = request.services.resolve(DIAGRAM)
            execution_orchestrator = request.services.resolve(EXECUTION_ORCHESTRATOR)
            prompt_builder = request.services.resolve(PROMPT_BUILDER)
            filesystem_adapter = request.services.resolve(FILESYSTEM_ADAPTER)
            
            # Debug logging
            logger.debug(f"[PersonJobHandler] Resolved services:")
            logger.debug(f"  - LLM Service: {llm_service is not None}")
            logger.debug(f"  - Diagram: {diagram is not None}")
            logger.debug(f"  - Orchestrator: {execution_orchestrator is not None}")
            logger.debug(f"  - Orchestrator type: {type(execution_orchestrator).__name__ if execution_orchestrator else 'None'}")
            logger.debug(f"  - Prompt Builder: {prompt_builder is not None}")
            logger.debug(f"  - Filesystem: {filesystem_adapter is not None}")
            
            # Set services on executors
            self.single_executor.set_services(
                llm_service=llm_service,
                diagram=diagram,
                execution_orchestrator=execution_orchestrator,
                prompt_builder=prompt_builder,
                filesystem_adapter=filesystem_adapter
            )
            
            # BatchExecutor uses SingleExecutor internally, so it inherits the services
            self._services_configured = True
        return None
    
    async def prepare_inputs(
        self,
        request: ExecutionRequest[PersonJobNode],
        inputs: dict[str, Envelope]
    ) -> dict[str, Any]:
        """Convert envelope inputs to data for person job.
        
        Envelopes allow clean, typed communication between nodes.
        """
        node = request.node
        
        # Store raw inputs for batch processing
        self._envelope_inputs = inputs
        
        # Extract prompt from envelope (optional, use default_prompt if not provided)
        prompt_envelope = self.get_optional_input(inputs, 'prompt')
        prompt = None
        if prompt_envelope:
            prompt = prompt_envelope.as_text()
        else:
            # Check if node has prompt_file configured (will be handled by single_executor)
            has_prompt_file = getattr(node, 'prompt_file', None) or getattr(node, 'first_prompt_file', None)

            # Use default_prompt from node configuration
            prompt = getattr(node, 'default_prompt', None)

            # Only raise error if no prompt sources are available
            if not prompt and not has_prompt_file:
                raise ValueError(f"No prompt provided and no default_prompt or prompt_file configured for node {node.id}")

        # Extract context (optional)
        context_data = None
        if context_envelope := self.get_optional_input(inputs, 'context'):
            try:
                context_data = context_envelope.as_json()
            except ValueError:
                # Fall back to text
                context_data = context_envelope.as_text()

        # Get conversation state if needed (based on memory_profile)
        conversation_state = None
        if conv_envelope := self.get_optional_input(inputs, '_conversation'):
            conversation_state = conv_envelope.as_conversation()
            
        # Prepare request with extracted inputs
        # Only override inputs if we extracted them from envelopes
        # Otherwise keep original inputs for single_executor to handle prompt_file
        if prompt is not None or context_data is not None:
            # Convert envelope inputs to plain values for executors
            processed_inputs = {}
            # Convert all envelope inputs to their values
            for key, envelope in inputs.items():
                if envelope.content_type == "raw_text":
                    processed_inputs[key] = envelope.as_text()
                elif envelope.content_type == "object":
                    processed_inputs[key] = envelope.as_json()
                elif envelope.content_type == "conversation_state":
                    processed_inputs[key] = envelope.as_conversation()
                else:
                    processed_inputs[key] = envelope.body
            
            # Override with explicit values if provided
            if prompt is not None:
                processed_inputs['prompt'] = prompt
            if context_data is not None:
                processed_inputs['context'] = context_data
            if conversation_state:
                processed_inputs['_conversation'] = conversation_state
                
            return processed_inputs
        else:
            # Keep original inputs for single_executor to process
            # Convert envelopes to plain values
            processed_inputs = {}
            for key, envelope in inputs.items():
                if envelope.content_type == "raw_text":
                    processed_inputs[key] = envelope.as_text()
                elif envelope.content_type == "object":
                    processed_inputs[key] = envelope.as_json()
                elif envelope.content_type == "conversation_state":
                    processed_inputs[key] = envelope.as_conversation()
                else:
                    processed_inputs[key] = envelope.body
            return processed_inputs
    
    async def run(
        self,
        inputs: dict[str, Any],
        request: ExecutionRequest[PersonJobNode]
    ) -> Any:
        """Execute person job with prepared inputs."""
        node = request.node
        
        # Update request inputs for executors
        request.inputs = inputs
        
        # Check if batch mode is enabled
        if getattr(node, 'batch', False):
            logger.info(f"Executing PersonJobNode {node.id} in batch mode")
            
            # Extract batch items from context
            batch_input_key = getattr(node, 'batch_input_key', 'items')
            items = None
            
            context_data = inputs.get('context')
            if context_data and isinstance(context_data, dict):
                items = context_data.get(batch_input_key)
            
            if not items:
                # Try to get from a dedicated batch input
                if batch_input_key in inputs:
                    items = inputs[batch_input_key]
            
            if items:
                request.inputs[batch_input_key] = items
            
            # Use batch executor for batch execution
            result = await self.batch_executor.execute(request)
            return result
        else:
            # Use single executor for normal execution
            result = await self.single_executor.execute(request)
            return result
    
    def serialize_output(
        self,
        result: Any,
        request: ExecutionRequest[PersonJobNode]
    ) -> Envelope:
        """Serialize person job result to envelope."""
        node = request.node
        trace_id = request.execution_id or ""
        
        # Check if batch mode
        if getattr(node, 'batch', False):
            # Convert batch result to envelope
            if hasattr(result, 'value'):
                output_envelope = EnvelopeFactory.json(
                    result.value,
                    produced_by=node.id,
                    trace_id=trace_id
                ).with_meta(
                    batch_mode=True,
                    person_id=node.person
                )
            else:
                output_envelope = EnvelopeFactory.text(
                    str(result),
                    produced_by=node.id,
                    trace_id=trace_id
                )
            return output_envelope
        else:
            # The single executor already returns an Envelope, just pass it through
            # SinglePersonJobExecutor.execute() returns properly typed envelopes:
            # - JSON envelope for structured output (text_format/text_format_file)
            # - Text envelope for regular text output
            # - Conversation envelope for conversation output
            if isinstance(result, Envelope):
                # Already a properly formatted envelope, return as-is
                return result
            else:
                # Fallback for unexpected result format (shouldn't happen)
                logger.warning(f"Unexpected result type from single_executor: {type(result)}")
                output_envelope = EnvelopeFactory.text(
                    str(result),
                    produced_by=node.id,
                    trace_id=trace_id
                )
                return output_envelope
    
    async def on_error(
        self,
        request: ExecutionRequest[PersonJobNode],
        error: Exception
    ) -> Optional[Envelope]:
        """Handle errors gracefully with envelope output."""
        trace_id = request.execution_id or ""
        
        # For ValueError (domain validation), only log in debug mode
        if isinstance(error, ValueError):
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Validation error in person job: {error}")
            return EnvelopeFactory.error(
                f"ValidationError: {error}",
                error_type="ValueError",
                produced_by=request.node.id,
                trace_id=trace_id
            )
        
        # For other errors, log them
        logger.error(f"Error executing person job: {error}")
        return EnvelopeFactory.error(
            str(error),
            error_type=error.__class__.__name__,
            produced_by=request.node.id,
            trace_id=trace_id
        )
    
    def post_execute(
        self,
        request: ExecutionRequest[PersonJobNode],
        output: Envelope
    ) -> Envelope:
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