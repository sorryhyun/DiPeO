"""Domain service for executing person jobs."""

import logging
from typing import Any

from dipeo.domain.services.arrow import MemoryTransformer, unwrap_inputs
from dipeo.domain.services.conversation import OnEveryTurnHandler
from dipeo.models import (
    DomainDiagram,
    ForgettingMode,
)

from .conversation_processor import ConversationProcessingService
from .output_builder import PersonJobOutputBuilder, PersonJobResult
from .prompt_service import PromptProcessingService

log = logging.getLogger(__name__)


class PersonJobExecutionService:
    """Service for executing person job business logic."""
    
    def __init__(
        self,
        prompt_service: PromptProcessingService,
        conversation_processor: ConversationProcessingService,
        output_builder: PersonJobOutputBuilder,
        on_every_turn_handler: OnEveryTurnHandler,
        memory_transformer: MemoryTransformer | None = None,
    ):
        self._prompt_service = prompt_service
        self._conversation_processor = conversation_processor
        self._output_builder = output_builder
        self._on_every_turn_handler = on_every_turn_handler
        self._memory_transformer = memory_transformer
    
    async def execute_person_job(
        self,
        person_id: str,
        node_id: str,
        prompt: str,
        first_only_prompt: str | None,
        forget_mode: ForgettingMode,
        model: str,
        api_key_id: str | None,
        system_prompt: str | None,
        inputs: dict[str, Any],
        diagram: DomainDiagram,
        execution_count: int,
        llm_client: Any,  # Will be protocol from core
        tools: list[Any] | None = None,
        conversation_service: Any | None = None,
        execution_id: str | None = None,
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
        person_label = person_id  # Default to person_id
        if conversation_service and hasattr(conversation_service, 'get_person_config'):
            person_config = conversation_service.get_person_config(person_id)
            if person_config and 'name' in person_config:
                person_label = person_config['name']
        else:
            # Fallback to using conversation processor with diagram
            person_label = self._conversation_processor.get_person_label(person_id, diagram)
        
        # Set execution context on conversation service if provided
        if conversation_service and hasattr(conversation_service, 'current_execution_id'):
            conversation_service.current_execution_id = execution_id
        
        # Handle memory transformation if using new arrow processing
        transformed_inputs = inputs
        if self._memory_transformer:
            # Check if inputs are already wrapped from arrow processing
            has_wrapped_inputs = any(
                isinstance(v, dict) and "arrow_metadata" in v 
                for v in inputs.values()
            )
            
            if has_wrapped_inputs:
                # Apply memory transformation to wrapped inputs
                memory_config = {"forget_mode": forget_mode.value}
                transformed_inputs = self._memory_transformer.transform_input(
                    inputs, "person_job", execution_count, memory_config
                )
                # Unwrap for use in the handler
                transformed_inputs = unwrap_inputs(transformed_inputs)
            else:
                # Legacy path - inputs not wrapped, use original logic
                transformed_inputs = inputs
        
        # Handle legacy memory forgetting if conversation service is provided
        # This is kept for backward compatibility when not using MemoryTransformer
        if conversation_service and not self._memory_transformer:
            if self.should_forget_messages(execution_count, forget_mode):
                conversation_service.forget_own_messages_for_person(person_id)
        
        # Prepare template values
        template_values = self._prepare_template_values(transformed_inputs)
        
        # Get and process prompt
        processed_prompt = self._prompt_service.get_prompt_for_execution(
            prompt, first_only_prompt, execution_count, template_values
        )
        
        # Handle conversation inputs and memory
        messages = await self._prepare_messages(
            prompt=processed_prompt,
            forget_mode=forget_mode,
            system_prompt=system_prompt,
            inputs=transformed_inputs,
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
            from dipeo.domain.services.conversation.message_builder_service import (
                MessageBuilderService,
            )
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
    
    async def execute_person_job_with_validation(
        self,
        person_id: str,
        node_id: str,
        props: Any,  # PersonJobNodeData
        inputs: dict[str, Any],
        diagram: DomainDiagram,
        execution_count: int,
        llm_client: Any,
        conversation_service: Any | None = None,
        execution_id: str | None = None,
    ) -> PersonJobResult:
        """Execute person job with validation."""
        # Get person configuration from conversation service if available
        person_config = None
        if conversation_service and hasattr(conversation_service, 'get_person_config'):
            person_config = conversation_service.get_person_config(person_id)
        
        # If not available from conversation service, fall back to diagram validation
        if not person_config:
            person = self._validate_person(person_id, diagram)
            model = person.llm_config.model if person.llm_config else "gpt-4.1-nano"
            api_key_id = person.llm_config.api_key_id if person.llm_config else None
            system_prompt = person.llm_config.system_prompt if person.llm_config else None
        else:
            # Use configuration from conversation service
            model = person_config.get('model', 'gpt-4.1-nano')
            api_key_id = person_config.get('api_key_id')
            system_prompt = person_config.get('system_prompt')
        
        # Extract configuration from props
        forget_mode = ForgettingMode.no_forget
        if props.memory_config and props.memory_config.forget_mode:
            forget_mode = ForgettingMode(props.memory_config.forget_mode)
        
        # Execute with all parameters
        result = await self.execute_person_job(
            person_id=person_id,
            node_id=node_id,
            prompt=props.default_prompt or "",
            first_only_prompt=props.first_only_prompt,
            forget_mode=forget_mode,
            model=model,
            api_key_id=api_key_id,
            system_prompt=system_prompt,
            inputs=inputs,
            diagram=diagram,
            execution_count=execution_count,
            llm_client=llm_client,
            tools=props.tools,
            conversation_service=conversation_service,
            execution_id=execution_id,
        )
        
        # Add model to metadata
        if result.metadata is None:
            result.metadata = {}
        result.metadata["model"] = model
        
        return result
    
    def _validate_person(self, person_id: str, diagram: DomainDiagram) -> Any:
        """Validate person exists in diagram."""
        if not diagram or not diagram.persons:
            raise ValueError("No persons defined in diagram")
        
        for person in diagram.persons:
            if person.id == person_id:
                return person
        
        raise ValueError(f"Person not found: {person_id}")
    
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
        system_prompt: str | None,
        inputs: dict[str, Any],
        diagram: DomainDiagram,
        execution_count: int,
        person_id: str,
        conversation_service: Any | None = None,
        execution_id: str | None = None,
    ) -> list[dict[str, Any]]:
        """Prepare messages for LLM execution."""
        messages = []
        
        # Handle system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Handle conversation inputs
        if self._conversation_processor.has_conversation_state_input(inputs, diagram):
            # Check if memory transformation was already applied
            memory_already_applied = self._memory_transformer is not None
            
            if not memory_already_applied:
                # Legacy path: Apply forgetting logic here
                if forget_mode == ForgettingMode.on_every_turn:
                    consolidated = await self._handle_on_every_turn_mode(
                        inputs, diagram, person_id
                    )
                    if consolidated:
                        messages.append({"role": "user", "content": consolidated})
                else:
                    # Add conversation messages directly
                    conversation_messages = self._extract_conversation_messages(inputs)
                    messages.extend(conversation_messages)
            else:
                # New path: Memory transformation already applied
                # Just extract messages normally
                conversation_messages = self._extract_conversation_messages(inputs)
                messages.extend(conversation_messages)
        
        # Add current prompt
        if prompt:
            messages.append({"role": "user", "content": prompt})
            
            # Store in conversation service if provided
            if conversation_service and execution_id:
                from dipeo.domain.services.conversation.message_builder_service import (
                    MessageBuilderService,
                )
                message_builder = MessageBuilderService(conversation_service, person_id, execution_id)
                message_builder.user(prompt)
        
        # Apply forgetting if needed (only in legacy path)
        if not self._memory_transformer and self.should_forget_messages(execution_count, forget_mode):
            messages = self._apply_forgetting(messages)
        
        return messages
    
    async def _handle_on_every_turn_mode(
        self,
        inputs: dict[str, Any],
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
        inputs: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """Extract conversation messages from inputs."""
        messages = []
        
        for value in inputs.values():
            if isinstance(value, dict) and "messages" in value:
                for msg in value["messages"]:
                    if isinstance(msg, dict):
                        messages.append({
                            "role": msg.get("role", "user"),
                            "content": msg.get("content", ""),
                            "tool_calls": msg.get("tool_calls"),
                            "tool_call_id": msg.get("tool_call_id"),
                        })
        
        return messages
    
    def _apply_forgetting(
        self,
        messages: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """Apply forgetting strategy to messages."""
        # Keep system messages and the last user message
        system_messages = [m for m in messages if m.get("role") == "system"]
        user_messages = [m for m in messages if m.get("role") == "user"]
        
        if user_messages:
            return system_messages + [user_messages[-1]]
        return system_messages
    
    def _prepare_template_values(
        self,
        inputs: dict[str, Any],
    ) -> dict[str, Any]:
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
        messages: list[dict[str, Any]],
        model: str,
        api_key: str | None,
        llm_client: Any,
        tools: list[Any] | None = None,
    ) -> Any:
        """Execute the LLM call."""
        # Messages are already in dict format expected by LLM service
        message_dicts = messages
        
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