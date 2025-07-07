"""Domain service for executing person jobs."""

from typing import Any, Dict, List, Optional
import logging

from dipeo.models import (
    DomainDiagram,
    Message,
    ForgettingMode,
)
from dipeo.domain.domains.conversation import OnEveryTurnHandler
from .prompt_service import PromptProcessingService
from .conversation_processor import ConversationProcessingService
from .output_builder import PersonJobOutputBuilder, PersonJobResult

log = logging.getLogger(__name__)


class PersonJobExecutionService:
    """Service for executing person job business logic."""
    
    def __init__(
        self,
        prompt_service: PromptProcessingService,
        conversation_processor: ConversationProcessingService,
        output_builder: PersonJobOutputBuilder,
        on_every_turn_handler: OnEveryTurnHandler,
    ):
        self._prompt_service = prompt_service
        self._conversation_processor = conversation_processor
        self._output_builder = output_builder
        self._on_every_turn_handler = on_every_turn_handler
    
    async def execute_person_job(
        self,
        person_id: str,
        node_id: str,
        prompt: str,
        first_only_prompt: Optional[str],
        forget_mode: ForgettingMode,
        model: str,
        api_key_id: Optional[str],
        system_prompt: Optional[str],
        inputs: Dict[str, Any],
        diagram: DomainDiagram,
        execution_count: int,
        llm_client: Any,  # Will be protocol from core
        tools: Optional[List[Any]] = None,
        conversation_service: Optional[Any] = None,
        execution_id: Optional[str] = None,
    ) -> PersonJobResult:
        """Execute a person job with all business logic.
        
        This encapsulates:
        - Prompt selection and processing
        - Memory/forgetting strategy
        - Conversation input handling
        - LLM execution
        - Output building
        """
        # Get person label for outputs
        person_label = self._conversation_processor.get_person_label(person_id, diagram)
        
        # Set execution context on conversation service if provided
        if conversation_service and hasattr(conversation_service, 'current_execution_id'):
            conversation_service.current_execution_id = execution_id
        
        # Handle memory forgetting if conversation service is provided
        if conversation_service and self.should_forget_messages(execution_count, forget_mode):
            conversation_service.forget_own_messages_for_person(person_id)
        
        # Prepare template values
        template_values = self._prepare_template_values(inputs)
        
        # Get and process prompt
        processed_prompt = self._prompt_service.get_prompt_for_execution(
            prompt, first_only_prompt, execution_count, template_values
        )
        
        # Handle conversation inputs and memory
        messages = await self._prepare_messages(
            prompt=processed_prompt,
            forget_mode=forget_mode,
            system_prompt=system_prompt,
            inputs=inputs,
            diagram=diagram,
            execution_count=execution_count,
            person_id=person_id,
            conversation_service=conversation_service,
            execution_id=execution_id,
        )
        
        # Execute LLM call
        response = await self._execute_llm_call(
            messages=messages,
            model=model,
            api_key=api_key_id,
            llm_client=llm_client,
            tools=tools,
        )
        
        # Extract content and usage from ChatResult
        content = response.text if hasattr(response, 'text') else str(response)
        usage = None
        tool_outputs = None
        
        if hasattr(response, 'token_usage') and response.token_usage:
            usage = {
                "input": response.token_usage.input,
                "output": response.token_usage.output,
                "total": response.token_usage.total if hasattr(response.token_usage, 'total') else (response.token_usage.input + response.token_usage.output)
            }
        
        if hasattr(response, 'tool_outputs') and response.tool_outputs:
            tool_outputs = [
                output.model_dump() for output in response.tool_outputs
            ]
        
        # Store the assistant response in conversation service if provided
        if conversation_service:
            from dipeo.domain.domains.conversation.message_builder_service import MessageBuilderService
            message_builder = MessageBuilderService(conversation_service, person_id, execution_id)
            message_builder.assistant(content)
        
        # Build output
        needs_conversation = self._conversation_processor.needs_conversation_output(
            node_id, diagram
        )
        
        # Get conversation messages if needed
        conversation_messages = []
        if needs_conversation and conversation_service:
            conversation_messages = conversation_service.get_messages_with_person_id(
                person_id, forget_mode=forget_mode
            )
        
        return self._output_builder.build_output(
            content=content,
            messages=conversation_messages,
            person_label=person_label,
            needs_conversation=needs_conversation,
            usage=usage,
            tool_outputs=tool_outputs,
        )
    
    def should_forget_messages(
        self,
        execution_count: int,
        forget_mode: ForgettingMode,
    ) -> bool:
        """Determine if messages should be forgotten based on mode and execution count."""
        if forget_mode == ForgettingMode.no_forget:
            return False
        elif forget_mode == ForgettingMode.on_every_turn:
            return execution_count > 0
        elif forget_mode == ForgettingMode.upon_request:
            # This would be handled by explicit user request
            return False
        return False
    
    async def _prepare_messages(
        self,
        prompt: str,
        forget_mode: ForgettingMode,
        system_prompt: Optional[str],
        inputs: Dict[str, Any],
        diagram: DomainDiagram,
        execution_count: int,
        person_id: str,
        conversation_service: Optional[Any] = None,
        execution_id: Optional[str] = None,
    ) -> List[Message]:
        """Prepare messages for LLM execution."""
        messages = []
        
        # Handle system prompt
        if system_prompt:
            messages.append(Message(role="system", content=system_prompt))
        
        # Handle conversation inputs
        if self._conversation_processor.has_conversation_state_input(inputs, diagram):
            # Process based on forget mode
            if forget_mode == ForgettingMode.on_every_turn:
                consolidated = await self._handle_on_every_turn_mode(
                    inputs, diagram, person_id
                )
                if consolidated:
                    messages.append(Message(role="user", content=consolidated))
            else:
                # Add conversation messages directly
                conversation_messages = self._extract_conversation_messages(inputs)
                messages.extend(conversation_messages)
        
        # Add current prompt
        if prompt:
            messages.append(Message(role="user", content=prompt))
            
            # Store in conversation service if provided
            if conversation_service and execution_id:
                from dipeo.domain.domains.conversation.message_builder_service import MessageBuilderService
                message_builder = MessageBuilderService(conversation_service, person_id, execution_id)
                message_builder.user(prompt)
        
        # Apply forgetting if needed
        if self.should_forget_messages(execution_count, forget_mode):
            messages = self._apply_forgetting(messages)
        
        return messages
    
    async def _handle_on_every_turn_mode(
        self,
        inputs: Dict[str, Any],
        diagram: DomainDiagram,
        person_id: str,
    ) -> str:
        """Handle on_every_turn mode processing."""
        used_keys = set()
        
        # Use conversation processor to consolidate messages
        return self._conversation_processor.consolidate_on_every_turn_messages(
            inputs, used_keys, diagram
        )
    
    def _extract_conversation_messages(
        self,
        inputs: Dict[str, Any],
    ) -> List[Message]:
        """Extract conversation messages from inputs."""
        messages = []
        
        for value in inputs.values():
            if isinstance(value, dict) and "messages" in value:
                for msg in value["messages"]:
                    if isinstance(msg, dict):
                        messages.append(
                            Message(
                                role=msg.get("role", "user"),
                                content=msg.get("content", ""),
                                tool_calls=msg.get("tool_calls"),
                                tool_call_id=msg.get("tool_call_id"),
                            )
                        )
        
        return messages
    
    def _apply_forgetting(
        self,
        messages: List[Message],
    ) -> List[Message]:
        """Apply forgetting strategy to messages."""
        # Keep system messages and the last user message
        system_messages = [m for m in messages if m.role == "system"]
        user_messages = [m for m in messages if m.role == "user"]
        
        if user_messages:
            return system_messages + [user_messages[-1]]
        return system_messages
    
    def _prepare_template_values(
        self,
        inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare values for template substitution."""
        # Filter out complex objects that shouldn't be in templates
        template_values = {}
        
        for key, value in inputs.items():
            # Skip conversation states and complex objects
            if isinstance(value, (str, int, float, bool)):
                template_values[key] = value
            elif isinstance(value, dict) and "messages" not in value:
                # Simple dict might be okay
                if all(isinstance(v, (str, int, float, bool)) for v in value.values()):
                    template_values[key] = value
        
        return template_values
    
    async def _execute_llm_call(
        self,
        messages: List[Message],
        model: str,
        api_key: Optional[str],
        llm_client: Any,
        tools: Optional[List[Any]] = None,
    ) -> Any:
        """Execute the LLM call."""
        # Convert Message objects to dict format expected by LLM service
        message_dicts = [
            {
                "role": msg.role,
                "content": msg.content,
                "tool_calls": msg.tool_calls,
                "tool_call_id": msg.tool_call_id,
            }
            for msg in messages
        ]
        
        # Build options if tools are provided
        options = None
        if tools:
            from dipeo.models import LLMRequestOptions
            options = LLMRequestOptions(tools=tools)
        
        # This will use the protocol from core
        return await llm_client.complete(
            messages=message_dicts,
            model=model,
            api_key_id=api_key,  # LLM service expects api_key_id, not api_key
            options=options,
        )