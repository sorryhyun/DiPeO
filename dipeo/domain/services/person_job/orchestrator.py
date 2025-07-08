"""Domain service that orchestrates person job execution using focused services."""

from typing import Any, Dict, List, Optional

from dipeo.models import ForgettingMode, DomainDiagram
from dipeo.domain.services.prompt.builder import PromptBuilder
from dipeo.domain.services.conversation.state_manager import ConversationStateManager
from dipeo.domain.services.conversation.message_preparator import MessagePreparator
from dipeo.domain.services.llm.executor import LLMExecutor, LLMExecutionResult
from dipeo.domain.services.arrow import MemoryTransformer, unwrap_inputs

from .output_builder import PersonJobOutputBuilder, PersonJobResult
from .conversation_processor import ConversationProcessingService


class PersonJobOrchestrator:
    """Orchestrates person job execution by coordinating focused services.
    
    Single Responsibility: Coordinate the execution flow between services.
    """
    
    def __init__(
        self,
        prompt_builder: PromptBuilder,
        conversation_state_manager: ConversationStateManager,
        message_preparator: MessagePreparator,
        llm_executor: LLMExecutor,
        output_builder: PersonJobOutputBuilder,
        conversation_processor: ConversationProcessingService,
        memory_transformer: Optional[MemoryTransformer] = None,
    ):
        self._prompt_builder = prompt_builder
        self._conversation_state_manager = conversation_state_manager
        self._message_preparator = message_preparator
        self._llm_executor = llm_executor
        self._output_builder = output_builder
        self._conversation_processor = conversation_processor
        self._memory_transformer = memory_transformer
    
    async def execute(
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
        llm_client: Any,
        template_service: Any,  # Template substitution service
        tools: Optional[List[Any]] = None,
        conversation_service: Optional[Any] = None,
        execution_id: Optional[str] = None,
    ) -> PersonJobResult:
        """Execute a person job by orchestrating focused services.
        
        This method coordinates:
        1. Input transformation (memory handling)
        2. Prompt building
        3. Conversation state management
        4. Message preparation
        5. LLM execution
        6. Output building
        """
        # Step 1: Handle memory transformation
        transformed_inputs = self._apply_memory_transformation(
            inputs, forget_mode, execution_count
        )
        
        # Step 2: Apply legacy forgetting if needed
        if conversation_service and not self._memory_transformer:
            if self._conversation_state_manager.should_forget_messages(
                execution_count, forget_mode
            ):
                conversation_service.forget_own_messages_for_person(person_id)
        
        # Step 3: Build prompt
        template_values = self._prompt_builder.prepare_template_values(
            transformed_inputs
        )
        
        built_prompt = self._prompt_builder.build_prompt(
            default_prompt=prompt,
            first_only_prompt=first_only_prompt,
            execution_count=execution_count,
            template_values=template_values,
            template_substitutor=template_service,
        )
        
        # Step 4: Prepare messages
        messages = await self._prepare_messages_for_execution(
            built_prompt=built_prompt,
            system_prompt=system_prompt,
            inputs=transformed_inputs,
            forget_mode=forget_mode,
            execution_count=execution_count,
            person_id=person_id,
            diagram=diagram,
            conversation_service=conversation_service,
            execution_id=execution_id,
        )
        
        # Step 5: Execute LLM call
        llm_result = await self._llm_executor.execute(
            messages=messages,
            model=model,
            api_key_id=api_key_id,
            llm_client=llm_client,
            tools=tools,
        )
        
        # Step 6: Store assistant response if needed
        if conversation_service:
            self._store_assistant_response(
                conversation_service,
                person_id,
                execution_id,
                llm_result.content,
            )
        
        # Step 7: Build and return output
        return self._build_final_output(
            llm_result=llm_result,
            person_id=person_id,
            node_id=node_id,
            diagram=diagram,
            forget_mode=forget_mode,
            conversation_service=conversation_service,
            model=model,
        )
    
    def _apply_memory_transformation(
        self,
        inputs: Dict[str, Any],
        forget_mode: ForgettingMode,
        execution_count: int,
    ) -> Dict[str, Any]:
        """Apply memory transformation if configured."""
        if not self._memory_transformer:
            return inputs
        
        # Check if inputs are already wrapped from arrow processing
        has_wrapped_inputs = any(
            isinstance(v, dict) and "arrow_metadata" in v 
            for v in inputs.values()
        )
        
        if has_wrapped_inputs:
            # Apply memory transformation to wrapped inputs
            memory_config = {"forget_mode": forget_mode.value}
            transformed = self._memory_transformer.transform_input(
                inputs, "person_job", execution_count, memory_config
            )
            # Unwrap for use
            return unwrap_inputs(transformed)
        
        return inputs
    
    async def _prepare_messages_for_execution(
        self,
        built_prompt: str,
        system_prompt: Optional[str],
        inputs: Dict[str, Any],
        forget_mode: ForgettingMode,
        execution_count: int,
        person_id: str,
        diagram: DomainDiagram,
        conversation_service: Optional[Any],
        execution_id: Optional[str],
    ) -> List[Dict[str, Any]]:
        """Prepare messages for LLM execution."""
        # Extract conversation messages if present
        conversation_messages = []
        
        if self._conversation_state_manager.has_conversation_input(inputs):
            memory_already_applied = self._memory_transformer is not None
            
            if not memory_already_applied and forget_mode == ForgettingMode.on_every_turn:
                # Handle on_every_turn consolidation
                person_labels = self._get_person_labels_for_inputs(inputs, diagram)
                consolidated = self._conversation_state_manager.consolidate_conversation_messages(
                    inputs, person_labels
                )
                if consolidated:
                    conversation_messages = [{"role": "user", "content": consolidated}]
            else:
                # Extract messages normally
                conversation_messages = self._conversation_state_manager.extract_conversation_messages(
                    inputs
                )
        
        # Store user prompt in conversation if needed
        if built_prompt and conversation_service and execution_id:
            self._store_user_message(
                conversation_service,
                person_id,
                execution_id,
                built_prompt,
            )
        
        # Apply forgetting if needed (legacy path)
        if not self._memory_transformer and self._conversation_state_manager.should_forget_messages(
            execution_count, forget_mode
        ):
            conversation_messages = self._conversation_state_manager.apply_forgetting_strategy(
                conversation_messages, forget_mode
            )
        
        # Prepare final messages
        return self._message_preparator.prepare_messages(
            system_prompt=system_prompt,
            conversation_messages=conversation_messages,
            current_prompt=built_prompt,
        )
    
    def _get_person_labels_for_inputs(
        self,
        inputs: Dict[str, Any],
        diagram: DomainDiagram,
    ) -> Dict[str, str]:
        """Get person labels for input keys."""
        labels = {}
        for key in inputs.keys():
            label = self._conversation_processor._find_person_label_for_key(
                key, diagram
            )
            if label:
                labels[key] = label
        return labels
    
    def _store_user_message(
        self,
        conversation_service: Any,
        person_id: str,
        execution_id: str,
        content: str,
    ) -> None:
        """Store user message in conversation service."""
        from dipeo.domain.services.conversation.message_builder_service import (
            MessageBuilderService,
        )
        message_builder = MessageBuilderService(
            conversation_service, person_id, execution_id
        )
        message_builder.user(content)
    
    def _store_assistant_response(
        self,
        conversation_service: Any,
        person_id: str,
        execution_id: Optional[str],
        content: str,
    ) -> None:
        """Store assistant response in conversation service."""
        from dipeo.domain.services.conversation.message_builder_service import (
            MessageBuilderService,
        )
        message_builder = MessageBuilderService(
            conversation_service, person_id, execution_id
        )
        message_builder.assistant(content)
    
    def _build_final_output(
        self,
        llm_result: LLMExecutionResult,
        person_id: str,
        node_id: str,
        diagram: DomainDiagram,
        forget_mode: ForgettingMode,
        conversation_service: Optional[Any],
        model: str,
    ) -> PersonJobResult:
        """Build the final output."""
        # Get person label
        person_label = self._get_person_label(
            person_id, diagram, conversation_service
        )
        
        # Check if conversation output is needed
        needs_conversation = self._conversation_processor.needs_conversation_output(
            node_id, diagram
        )
        
        # Get conversation messages if needed
        conversation_messages = []
        if needs_conversation and conversation_service:
            conversation_messages = conversation_service.get_messages_with_person_id(
                person_id, forget_mode=forget_mode
            )
        
        # Build output
        result = self._output_builder.build_output(
            content=llm_result.content,
            messages=conversation_messages,
            person_label=person_label,
            needs_conversation=needs_conversation,
            usage=llm_result.usage,
            tool_outputs=llm_result.tool_outputs,
        )
        
        # Add model to metadata
        if result.metadata is None:
            result.metadata = {}
        result.metadata["model"] = model
        
        return result
    
    def _get_person_label(
        self,
        person_id: str,
        diagram: DomainDiagram,
        conversation_service: Optional[Any],
    ) -> str:
        """Get person label from conversation service or diagram."""
        # Try conversation service first
        if conversation_service and hasattr(conversation_service, 'get_person_config'):
            person_config = conversation_service.get_person_config(person_id)
            if person_config and 'name' in person_config:
                return person_config['name']
        
        # Fall back to diagram
        return self._conversation_processor.get_person_label(person_id, diagram)