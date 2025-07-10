"""Domain service that orchestrates person job execution using focused services."""

from typing import Any, Dict, List, Optional

from dipeo.models import ForgettingMode, DomainDiagram
from dipeo.application.utils.template import PromptBuilder
from dipeo.utils.conversation.state_utils import ConversationStateManager
from dipeo.utils.conversation.message_formatter import MessageFormatter
from dipeo.application.services.llm import LLMExecutor, LLMExecutionResult
from dipeo.utils.arrow import MemoryTransformer, unwrap_inputs

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
        llm_executor: LLMExecutor,
        output_builder: PersonJobOutputBuilder,
        conversation_processor: ConversationProcessingService,
        memory_transformer: Optional[MemoryTransformer] = None,
    ):
        self._prompt_builder = prompt_builder
        self._conversation_state_manager = conversation_state_manager
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
        
        # Debug logging for inputs
        import logging
        logger = logging.getLogger(__name__)
        if execution_count > 0:
            logger.debug(f"Person {person_id} execution #{execution_count} inputs: {list(transformed_inputs.keys())}")
            for key, value in transformed_inputs.items():
                if isinstance(value, dict) and "messages" in value:
                    logger.debug(f"  Input '{key}' has {len(value['messages'])} messages")
        
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
            template_substitutor=None,
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
        """Apply memory transformation if configured.
        
        IMPORTANT: Memory transformation (forgetting) should NOT be applied to
        inputs from other nodes. It should only apply to the person's own
        conversation history loaded from storage. Inputs from other panels
        should be preserved as-is to maintain inter-panel communication.
        """
        # Always unwrap inputs to handle arrow-processed values
        # The unwrap_inputs function safely handles both wrapped and unwrapped inputs
        return unwrap_inputs(inputs)
    
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
            
            # Always extract messages normally to preserve conversation structure
            conversation_messages = self._conversation_state_manager.extract_conversation_messages(
                inputs
            )
            
            # If memory not already applied and we're in on_every_turn mode,
            # the forgetting will be applied later in this method (lines 207-214)
        
        # Store user prompt in conversation if needed
        if built_prompt and conversation_service and execution_id:
            self._store_user_message(
                conversation_service,
                person_id,
                execution_id,
                built_prompt,
            )
        
        # Apply forgetting if needed (legacy path)
        # IMPORTANT: Do NOT apply forgetting to messages from inputs (other panels).
        # Forgetting should only apply to the person's own conversation history.
        # The conversation_messages at this point come from inputs, so we should
        # NOT apply forgetting strategy here.
        
        # Prepare final messages
        return MessageFormatter.prepare_messages(
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
        # Set execution_id first if the service supports it
        if hasattr(conversation_service, 'current_execution_id'):
            conversation_service.current_execution_id = execution_id
        
        # Store user message directly
        conversation_service.add_message(
            person_id=person_id,
            role="user",
            content=content
        )
    
    def _store_assistant_response(
        self,
        conversation_service: Any,
        person_id: str,
        execution_id: Optional[str],
        content: str,
    ) -> None:
        """Store assistant message in conversation service."""
        # Set execution_id first if the service supports it
        if execution_id and hasattr(conversation_service, 'current_execution_id'):
            conversation_service.current_execution_id = execution_id
        
        # Store assistant message directly
        conversation_service.add_message(
            person_id=person_id,
            role="assistant",
            content=content
        )
    
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
    
    async def execute_person_job_with_validation(
        self,
        person_id: str,
        node_id: str,
        props: Any,  # PersonJobNodeData
        inputs: Dict[str, Any],
        diagram: DomainDiagram,
        execution_count: int,
        llm_client: Any,
        conversation_service: Optional[Any] = None,
        execution_id: Optional[str] = None,
    ) -> PersonJobResult:
        """Execute person job with validation.
        
        This method provides backward compatibility with PersonJobExecutionService.
        It extracts configuration from props and calls the core execute method.
        """
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
        result = await self.execute(
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
        
        # Model is already added to metadata in execute method
        return result
    
    def _validate_person(self, person_id: str, diagram: DomainDiagram) -> Any:
        """Validate person exists in diagram."""
        if not diagram or not diagram.persons:
            raise ValueError("No persons defined in diagram")
        
        for person in diagram.persons:
            if person.id == person_id:
                return person
        
        raise ValueError(f"Person not found: {person_id}")