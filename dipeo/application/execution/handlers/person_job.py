
import logging
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.types import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.unified_service_registry import (
    LLM_SERVICE,
    DIAGRAM,
    CONVERSATION_MANAGER,
    PROMPT_BUILDER
)
from dipeo.core.dynamic import Person
from dipeo.core.static.generated_nodes import PersonJobNode
from dipeo.core.execution.node_output import ConversationOutput, TextOutput, NodeOutputProtocol, ErrorOutput
from dipeo.models import (
    MemorySettings,
    Message,
    NodeType,
    PersonID,
    PersonJobNodeData,
)

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


@register_handler
class PersonJobNodeHandler(TypedNodeHandler[PersonJobNode]):
    
    def __init__(self):
        # Person cache managed at handler level
        self._person_cache: dict[str, Person] = {}


    @property
    def node_class(self) -> type[PersonJobNode]:
        return PersonJobNode
    
    @property
    def node_type(self) -> str:
        return NodeType.person_job.value

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
        ]

    @property
    def description(self) -> str:
        return "Execute person job with conversation memory"
    
    def validate(self, request: ExecutionRequest[PersonJobNode]) -> Optional[str]:
        """Validate the execution request."""
        if not request.node.person_id:
            return "No person specified"
        
        # Check max iteration
        execution_count = request.context.get_node_execution_count(request.node_id)
        if execution_count > request.node.max_iteration:
            return f"Max iteration ({request.node.max_iteration}) reached"
            
        return None
    
    async def execute_request(self, request: ExecutionRequest[PersonJobNode]) -> NodeOutputProtocol:
        """Execute the person job with the unified request object."""
        # Get node and context from request
        node = request.node
        context = request.context
        
        # Get inputs from request (already resolved by engine)
        inputs = request.inputs or {}
        
        # Direct typed access to person_id
        person_id = node.person_id

        # Get services from services dict
        llm_service = request.services.get(LLM_SERVICE.name)
        diagram = request.services.get(DIAGRAM.name)
        conversation_manager = request.services.get(CONVERSATION_MANAGER.name)
        prompt_builder = request.services.get(PROMPT_BUILDER.name)
        
        if not all([llm_service, diagram, conversation_manager, prompt_builder]):
            raise ValueError("Required services not available")
        

        execution_count = context.get_node_execution_count(node.id)

        try:
            # Get or create person
            person = self._get_or_create_person(person_id, conversation_manager)
            
            # Apply memory settings if configured
            # Note: We apply memory settings even on first execution because some nodes
            # (like judge panels) need to see full conversation history from the start
            if node.memory_settings:
                person.apply_memory_settings(node.memory_settings)
            
            # Use inputs directly
            transformed_inputs = inputs
            
            # Handle conversation inputs
            has_conversation_input = self._has_conversation_input(transformed_inputs)
            if has_conversation_input:
                self._rebuild_conversation(person, transformed_inputs)

            # Build prompt BEFORE applying memory management
            template_values = prompt_builder.prepare_template_values(
                transformed_inputs, 
                conversation_manager=conversation_manager,
                person_id=person_id
            )

            # Disable auto-prepend if we have conversation input (to avoid duplication)
            built_prompt = prompt_builder.build(
                prompt=node.default_prompt,
                first_only_prompt=node.first_only_prompt,
                execution_count=execution_count,
                template_values=template_values,
                auto_prepend_conversation=not has_conversation_input
            )

            # Skip if no prompt
            if not built_prompt:
                logger.warning(f"Skipping execution for person {person_id} - no prompt available")
                return TextOutput(
                    value="",
                    node_id=node.id,
                    metadata={"skipped": True, "reason": "No prompt available"}
                )
            
            # Execute LLM call
            # Only pass tools if they are configured
            complete_kwargs = {
                "prompt": built_prompt,
                "llm_service": llm_service,
                "from_person_id": "system",
                "temperature": 0.7,
                "max_tokens": 4096,
            }
            
            # Add tools only if they exist
            if node.tools:
                complete_kwargs["tools"] = node.tools
                
            result = await person.complete(**complete_kwargs)
            
            # Build and return output
            return self._build_node_output(
                result=result,
                person=person,
                node=node,
                diagram=diagram,
                model=person.llm_config.model
            )
            
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
    
    # _execute_with_props removed - logic integrated into execute method
    
    def _get_or_create_person(
        self,
        person_id: str,
        conversation_manager: Any
    ) -> Person:
        # Check cache first
        if person_id in self._person_cache:
            return self._person_cache[person_id]
        
        # Get person config from conversation manager
        person_config = None
        person_name = person_id  # Default to person_id as name
        
        if hasattr(conversation_manager, 'get_person_config'):
            person_config = conversation_manager.get_person_config(person_id)
        
        
        if not person_config:
            # Fallback: create minimal config with default LLM
            from dipeo.models import ApiKeyID, LLMService, PersonLLMConfig
            person_config = PersonLLMConfig(
                service=LLMService.openai,
                model="gpt-4.1-nano",
                api_key_id=ApiKeyID("")  # Wrap empty string with ApiKeyID
            )
        
        # Create Person object without conversation_manager to avoid circular reference
        person = Person(
            id=PersonID(person_id),
            name=person_name,
            llm_config=person_config,
            conversation_manager=None  # Initially None to avoid recursion
        )
        
        # Cache the person BEFORE setting conversation_manager
        self._person_cache[person_id] = person
        
        # Now safely set the conversation_manager after caching
        person._conversation_manager = conversation_manager
        
        return person
    
    def _has_conversation_input(self, inputs: dict[str, Any]) -> bool:
        # Check for conversation inputs in the same way the prompt builder does
        for key, value in inputs.items():
            # Check if key ends with _messages (like the prompt builder)
            if key.endswith('_messages') and isinstance(value, list):
                return True
            # Also check the original structure for backwards compatibility
            if isinstance(value, dict) and "messages" in value:
                return True
        return False
    
    def _rebuild_conversation(self, person: Person, inputs: dict[str, Any]) -> None:
        all_messages = []
        for key, value in inputs.items():
            if isinstance(value, dict) and "messages" in value:
                messages = value["messages"]
                if isinstance(messages, list):
                    all_messages.extend(messages)
        
        if not all_messages:
            logger.debug("_rebuild_conversation: No messages found in inputs")
            return
        
        logger.debug(f"_rebuild_conversation: Processing {len(all_messages)} total messages")
        
        for i, msg in enumerate(all_messages):
            # Handle both Message objects and dict formats
            if isinstance(msg, Message):
                # Already a Message object - check content and add directly
                if "[Previous conversation" not in msg.content:
                    person.add_message(msg)
            elif isinstance(msg, dict):
                # Dictionary format - convert to Message
                content = msg.get("content", "")
                # Skip messages that contain the "[Previous conversation" marker to avoid duplication
                if "[Previous conversation" in content:
                    continue
                    
                message = Message(
                    from_person_id=msg.get("from_person_id", person.id),
                    to_person_id=msg.get("to_person_id", person.id),
                    content=content,
                    message_type="person_to_person",
                    timestamp=msg.get("timestamp"),
                )
                person.add_message(message)
                logger.debug(f"  Added dict message {i}: from={message.from_person_id}, to={message.to_person_id}, content_length={len(content)}")
    
    def _needs_conversation_output(self, node_id: str, diagram: Any) -> bool:
        # Check if any edge from this node expects conversation output
        for edge in diagram.edges:
            if str(edge.source_node_id) == node_id:
                # Check for explicit conversation output
                if edge.source_output == "conversation":
                    return True
                # Check data_transform for content_type = conversation_state
                if hasattr(edge, 'data_transform') and edge.data_transform:
                    if edge.data_transform.get('content_type') == 'conversation_state':
                        return True
        return False
    
    def _build_node_output(self, result: Any, person: Person, node: PersonJobNode, diagram: Any, model: str) -> NodeOutputProtocol:
        # Build metadata
        metadata = {"model": model}
        
        # Check if conversation output is needed
        if self._needs_conversation_output(str(node.id), diagram):
            # Return ConversationOutput with messages
            messages = []
            for msg in person.get_messages():
                messages.append(msg)
            
            return ConversationOutput(
                value=messages,
                node_id=node.id,
                metadata=metadata
            )
        else:
            # Return TextOutput with just the text
            return TextOutput(
                value=result.text,
                node_id=node.id,
                metadata=metadata
            )
    
