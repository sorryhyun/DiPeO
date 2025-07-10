"""Enhanced PersonJobOrchestrator that integrates with ConversationManager."""

import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.services.llm import LLMExecutionResult, LLMExecutor
from dipeo.core.dynamic import Person
from dipeo.models import DomainDiagram, ForgettingMode, Message, PersonID
from dipeo.utils.arrow import MemoryTransformer, unwrap_inputs
from dipeo.utils.conversation.state_utils import ConversationStateManager
from dipeo.application.utils.template import PromptBuilder

from .conversation_processor import ConversationProcessingService
from .output_builder import PersonJobOutputBuilder, PersonJobResult

if TYPE_CHECKING:
    from dipeo.core.dynamic.conversation_manager import ConversationManager
    from dipeo.core.ports import LLMServicePort

logger = logging.getLogger(__name__)


class PersonJobOrchestratorV2:
    """Enhanced orchestrator that uses ConversationManager and Person objects.
    
    This orchestrator integrates with the new ConversationManager protocol while
    maintaining backward compatibility with existing conversation services.
    """
    
    def __init__(
        self,
        prompt_builder: PromptBuilder,
        conversation_state_manager: ConversationStateManager,
        llm_executor: LLMExecutor,
        output_builder: PersonJobOutputBuilder,
        conversation_processor: ConversationProcessingService,
        memory_transformer: MemoryTransformer | None = None,
        conversation_manager: Optional["ConversationManager"] = None,
    ):
        self._prompt_builder = prompt_builder
        self._conversation_state_manager = conversation_state_manager
        self._llm_executor = llm_executor
        self._output_builder = output_builder
        self._conversation_processor = conversation_processor
        self._memory_transformer = memory_transformer
        self._conversation_manager = conversation_manager
        
        # Cache for Person objects
        self._person_cache: dict[str, Person] = {}
    
    def _get_or_create_person(
        self,
        person_id: str,
        diagram: DomainDiagram,
        conversation_service: Any | None = None
    ) -> Person:
        """Get or create a Person object."""
        # Check cache first
        if person_id in self._person_cache:
            return self._person_cache[person_id]
        
        # Find person in diagram
        person_data = None
        for p in diagram.persons:
            if p.id == person_id:
                person_data = p
                break
        
        if not person_data:
            raise ValueError(f"Person not found: {person_id}")
        
        # Create Person object
        person = Person(
            id=PersonID(person_id),
            name=person_data.label,
            llm_config=person_data.llm_config
        )
        
        # If we have a ConversationManager, sync the conversation
        if self._conversation_manager:
            conversation = self._conversation_manager.get_conversation(person_id)
            person.conversation = conversation
        
        # Cache the person
        self._person_cache[person_id] = person
        
        return person
    
    async def execute(
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
        llm_client: "LLMServicePort",
        tools: list[Any] | None = None,
        conversation_service: Any | None = None,
        execution_id: str | None = None,
    ) -> PersonJobResult:
        """Execute a person job using Person objects and ConversationManager."""
        
        # Get or create Person object
        person = self._get_or_create_person(person_id, diagram, conversation_service)
        
        # Handle memory transformation
        logger.debug(f"Raw inputs for {person_id}: {list(inputs.keys())}")
        transformed_inputs = self._apply_memory_transformation(
            inputs, forget_mode, execution_count
        )
        logger.debug(f"Transformed inputs for {person_id}: {list(transformed_inputs.keys())}")
        
        # Handle conversation inputs
        if self._conversation_processor.has_conversation_state_input(transformed_inputs, diagram):
            self._rebuild_conversation_from_inputs(
                person, transformed_inputs, forget_mode
            )
        
        # Apply forgetting if needed
        if (
            self._conversation_manager
            and execution_count > 0
            and self._conversation_state_manager.should_forget_messages(
                execution_count, forget_mode
            )
        ):
            self._conversation_manager.apply_forgetting(
                person_id, forget_mode, execution_id
            )
        
        # Build prompt
        template_values = self._prompt_builder.prepare_template_values(
            transformed_inputs
        )
        
        # Debug logging
        logger.debug(f"Template values for {person_id}: {template_values}")
        logger.debug(f"Prompt: '{prompt}', First only: '{first_only_prompt}', Exec count: {execution_count}")
        
        built_prompt = self._prompt_builder.build_prompt(
            default_prompt=prompt,
            first_only_prompt=first_only_prompt,
            execution_count=execution_count,
            template_values=template_values,
            template_substitutor=None,
        )
        
        logger.debug(f"Built prompt for {person_id}: '{built_prompt}'")
        
        # Skip execution if there's no prompt
        if not built_prompt:
            return PersonJobResult(
                content="",
                conversation_state={},
                metadata={"skipped": True, "reason": "No prompt available"},
                usage={},
                tool_outputs=None
            )
        
        # Use Person's chat method if we have a proper LLM service
        logger.debug(f"Checking llm_client: has 'complete'? {hasattr(llm_client, 'complete')}")
        if hasattr(llm_client, 'complete'):
            # Add user message
            user_message = Message(
                from_person_id="system",
                to_person_id=person.id,
                content=built_prompt,
                message_type="system_to_person",
                timestamp=datetime.utcnow().isoformat()
            )
            
            if self._conversation_manager:
                self._conversation_manager.add_message(
                    person_id, user_message, execution_id or "", node_id
                )
            else:
                person.add_message(user_message)
            
            # Execute with Person's chat method
            logger.debug(f"Executing chat for {person_id} with message: '{user_message.content}'")
            result = await person.chat(
                message=built_prompt,  # Pass the actual prompt
                llm_service=llm_client,
                from_person_id="system",
                memory_config=None,  # Memory already handled
                temperature=0.7,
                max_tokens=4096,
                tools=tools
            )
            
            llm_result = LLMExecutionResult(
                content=result.text,
                usage=result.token_usage,
                tool_outputs=None
            )
        else:
            # Fallback to legacy execution
            messages = self._prepare_messages_for_execution(
                person, system_prompt, built_prompt
            )
            
            logger.debug(f"Prepared messages for {person_id}: {len(messages)} messages")
            for i, msg in enumerate(messages):
                logger.debug(f"  Message {i}: role={msg.get('role')}, content_len={len(msg.get('content', ''))}")
            
            # Skip if no messages or only empty messages
            if not messages or all(not msg.get('content') for msg in messages):
                return PersonJobResult(
                    content="",
                    conversation_state={},
                    metadata={"skipped": True, "reason": "No prompt available"},
                    usage={},
                    tool_outputs=None
                )
            
            llm_result = await self._llm_executor.execute(
                messages=messages,
                model=model,
                api_key_id=api_key_id,
                llm_client=llm_client,
                tools=tools,
            )
            
            # Store messages in Person's conversation
            assistant_message = Message(
                from_person_id=person.id,
                to_person_id="system",
                content=llm_result.content,
                message_type="person_to_system",
                timestamp=datetime.utcnow().isoformat(),
                token_count=llm_result.usage.total if llm_result.usage else None
            )
            
            if self._conversation_manager:
                self._conversation_manager.add_message(
                    person_id, assistant_message, execution_id or "", node_id
                )
            else:
                person.add_message(assistant_message)
        
        # Build final output
        return self._build_final_output(
            llm_result=llm_result,
            person=person,
            node_id=node_id,
            diagram=diagram,
            forget_mode=forget_mode,
            model=model,
        )
    
    def _apply_memory_transformation(
        self,
        inputs: dict[str, Any],
        forget_mode: ForgettingMode,
        execution_count: int
    ) -> dict[str, Any]:
        """Apply memory transformation to inputs."""
        if self._memory_transformer:
            return self._memory_transformer.transform_input(
                inputs, "person_job", execution_count, 
                {"forget_mode": forget_mode.value}
            )
        return unwrap_inputs(inputs)
    
    def _rebuild_conversation_from_inputs(
        self,
        person: Person,
        inputs: dict[str, Any],
        forget_mode: ForgettingMode
    ) -> None:
        """Rebuild conversation from inputs."""
        # Extract conversation messages from inputs
        all_messages = []
        for value in inputs.values():
            if isinstance(value, dict) and "messages" in value:
                messages = value["messages"]
                if isinstance(messages, list):
                    all_messages.extend(messages)
        
        if not all_messages:
            return
        
        # Clear existing conversation if needed
        if forget_mode == ForgettingMode.on_every_turn:
            person.clear_conversation()
        
        # Add messages to person's conversation
        for msg_dict in all_messages:
            # Convert dict to Message object
            message = Message(
                from_person_id=msg_dict.get("from_person_id", person.id),
                to_person_id=msg_dict.get("to_person_id", person.id),
                content=msg_dict.get("content", ""),
                message_type="person_to_person",
                timestamp=msg_dict.get("timestamp"),
            )
            person.add_message(message)
    
    def _prepare_messages_for_execution(
        self,
        person: Person,
        system_prompt: str | None,
        user_prompt: str
    ) -> list[dict[str, str]]:
        """Prepare messages for LLM execution."""
        messages = []
        
        # Add system prompt
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # Add conversation history
        for msg in person.get_messages():
            if msg.from_person_id == person.id:
                role = "assistant"
            elif msg.from_person_id == "system":
                role = "system"
            else:
                role = "user"
            
            messages.append({"role": role, "content": msg.content})
        
        # Add current prompt
        messages.append({"role": "user", "content": user_prompt})
        
        return messages
    
    def _build_final_output(
        self,
        llm_result: LLMExecutionResult,
        person: Person,
        node_id: str,
        diagram: DomainDiagram,
        forget_mode: ForgettingMode,
        model: str,
    ) -> PersonJobResult:
        """Build the final output using Person's conversation."""
        # Check if conversation output is needed
        needs_conversation = self._conversation_processor.needs_conversation_output(
            node_id, diagram
        )
        
        # Get conversation messages if needed
        conversation_messages = []
        if needs_conversation:
            # Convert Person's messages to output format
            for msg in person.get_messages():
                conversation_messages.append({
                    "role": "assistant" if msg.from_person_id == person.id else "user",
                    "content": msg.content,
                    "person_id": person.id,
                    "person_label": person.name,
                })
        
        # Build output
        result = self._output_builder.build_output(
            content=llm_result.content,
            messages=conversation_messages,
            person_label=person.name,
            needs_conversation=needs_conversation,
            usage=llm_result.usage,
            tool_outputs=llm_result.tool_outputs,
        )
        
        # Add model to metadata
        if result.metadata is None:
            result.metadata = {}
        result.metadata["model"] = model
        
        return result
    
    async def execute_person_job_with_validation(
        self,
        person_id: str,
        node_id: str,
        props: Any,
        inputs: dict[str, Any],
        diagram: DomainDiagram,
        execution_count: int,
        llm_client: Any,
        conversation_service: Any | None = None,
        execution_id: str | None = None,
    ) -> PersonJobResult:
        """Execute person job with validation (backward compatibility method)."""
        # Get person from diagram
        person = self._get_or_create_person(person_id, diagram, conversation_service)
        
        # Extract configuration
        forget_mode = ForgettingMode.no_forget
        if props.memory_config and props.memory_config.forget_mode:
            forget_mode = ForgettingMode(props.memory_config.forget_mode)
        
        # Execute with all parameters
        return await self.execute(
            person_id=person_id,
            node_id=node_id,
            prompt=props.default_prompt or "",
            first_only_prompt=props.first_only_prompt,
            forget_mode=forget_mode,
            model=person.llm_config.model,
            api_key_id=person.llm_config.api_key_id,
            system_prompt=person.llm_config.system_prompt,
            inputs=inputs,
            diagram=diagram,
            execution_count=execution_count,
            llm_client=llm_client,
            tools=props.tools,
            conversation_service=conversation_service,
            execution_id=execution_id,
        )