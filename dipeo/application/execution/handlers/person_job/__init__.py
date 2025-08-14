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
from dipeo.application.execution.handler_base import EnvelopeNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.domain.conversation import Person
from dipeo.diagram_generated.generated_nodes import PersonJobNode, NodeType
from dipeo.core.execution.node_output import NodeOutputProtocol
from dipeo.core.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.models.person_job_model import PersonJobNodeData

from .single_executor import SinglePersonJobExecutor
from .batch_executor import BatchPersonJobExecutor

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@register_handler
class PersonJobNodeHandler(EnvelopeNodeHandler[PersonJobNode]):
    """Handler for executing AI person jobs with conversation memory.
    
    This handler supports both single person execution and batch execution
    for processing multiple items through the same person configuration.
    Routes execution to appropriate executor based on batch configuration.
    
    Now uses envelope-based communication for clean input/output interfaces.
    """
    
    # Enable envelope mode
    _expects_envelopes = True
    
    def __init__(self):
        super().__init__()
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
        return None
    
    async def execute_with_envelopes(
        self,
        request: ExecutionRequest[PersonJobNode],
        inputs: dict[str, Envelope]
    ) -> NodeOutputProtocol:
        """Execute person job with envelope inputs.
        
        Envelopes allow clean, typed communication between nodes.
        """
        node = request.node
        trace_id = request.execution_id or ""
        
        try:
            # Extract prompt from envelope (optional, use default_prompt if not provided)
            prompt_envelope = self.get_optional_input(inputs, 'prompt')
            if prompt_envelope:
                prompt = self.reader.as_text(prompt_envelope)
            else:
                # Use default_prompt from node configuration
                prompt = getattr(node, 'default_prompt', None)
                if not prompt:
                    raise ValueError(f"No prompt provided and no default_prompt configured for node {node.id}")
            
            # Extract context (optional)
            context_data = None
            if context_envelope := self.get_optional_input(inputs, 'context'):
                try:
                    context_data = self.reader.as_json(context_envelope)
                except ValueError:
                    # Fall back to text
                    context_data = self.reader.as_text(context_envelope)
            
            # Get conversation state if needed (based on memory_profile)
            conversation_state = None
            # Check if memory is enabled (memory_profile is not None or 'NONE')
            memory_enabled = node.memory_profile and node.memory_profile != 'NONE'
            if memory_enabled:
                if conv_envelope := self.get_optional_input(inputs, '_conversation'):
                    conversation_state = self.reader.as_conversation(conv_envelope)
            
            # Prepare request with extracted inputs
            # We need to update the request inputs for the executors
            request.inputs = {
                'prompt': prompt,
                'context': context_data,
            }
            if conversation_state:
                request.inputs['_conversation'] = conversation_state
            
            # Check if batch mode is enabled
            if getattr(node, 'batch', False):
                logger.info(f"Executing PersonJobNode {node.id} in batch mode")
                
                # Extract batch items from context envelope
                batch_input_key = getattr(node, 'batch_input_key', 'items')
                items = None
                
                if context_data and isinstance(context_data, dict):
                    items = context_data.get(batch_input_key)
                
                if not items:
                    # Try to get from a dedicated batch input
                    if batch_envelope := self.get_optional_input(inputs, batch_input_key):
                        items = self.reader.as_json(batch_envelope)
                
                if items:
                    request.inputs[batch_input_key] = items
                
                # Use batch executor for batch execution
                result = await self.batch_executor.execute(request)
                
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
                
                return self.create_success_output(output_envelope)
            else:
                # Use single executor for normal execution
                result = await self.single_executor.execute(request)
                
                # Extract response content and create envelope
                if hasattr(result, 'value'):
                    content = result.value
                    
                    # Check if it contains token usage metadata
                    token_usage = None
                    if isinstance(content, dict) and 'token_usage' in content:
                        token_usage = content.pop('token_usage')
                        # If only token_usage was in the dict, use the response text
                        if 'response' in content:
                            content = content['response']
                    
                    # Create output envelope
                    output_envelope = EnvelopeFactory.text(
                        content if isinstance(content, str) else str(content),
                        produced_by=node.id,
                        trace_id=trace_id
                    ).with_meta(
                        person_id=node.person
                    )
                    
                    if token_usage:
                        output_envelope = output_envelope.with_meta(token_usage=token_usage)
                    
                    # Add conversation update if needed
                    envelopes = [output_envelope]
                    # Check if memory is enabled and we have conversation update
                    if memory_enabled and hasattr(result, 'conversation_update'):
                        conv_envelope = EnvelopeFactory.conversation(
                            result.conversation_update,
                            produced_by=node.id,
                            trace_id=trace_id
                        )
                        envelopes.append(conv_envelope)
                    
                    return self.create_success_output(*envelopes)
                else:
                    # Fallback for unexpected result format
                    output_envelope = EnvelopeFactory.text(
                        str(result),
                        produced_by=node.id,
                        trace_id=trace_id
                    )
                    return self.create_success_output(output_envelope)
                    
        except Exception as e:
            return self.create_error_output(e, node.id, trace_id)
    
    async def on_error(
        self,
        request: ExecutionRequest[PersonJobNode],
        error: Exception
    ) -> Optional[NodeOutputProtocol]:
        """Handle errors gracefully with envelope output."""
        trace_id = request.execution_id or ""
        
        # For ValueError (domain validation), only log in debug mode
        if isinstance(error, ValueError):
            if logger.isEnabledFor(logging.DEBUG):
                logger.debug(f"Validation error in person job: {error}")
            return self.create_error_output(
                ValueError(f"ValidationError: {error}"),
                request.node.id,
                trace_id
            )
        
        # For other errors, log them
        logger.error(f"Error executing person job: {error}")
        return self.create_error_output(error, request.node.id, trace_id)
    
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