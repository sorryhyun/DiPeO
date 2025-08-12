"""Single person job executor - handles execution for a single person."""

import json
import logging
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.memory_profiles import MemoryProfile, MemoryProfileFactory
from dipeo.diagram_generated.generated_nodes import PersonJobNode
from dipeo.core.execution.node_output import ConversationOutput, TextOutput, NodeOutputProtocol, PersonJobOutput
from dipeo.diagram_generated.domain_models import Message, PersonID

from .prompt_resolver import PromptFileResolver
from .text_format_handler import TextFormatHandler
from .conversation_handler import ConversationHandler

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


class SinglePersonJobExecutor:
    """Executor for single person job execution."""
    
    def __init__(self, person_cache: dict[str, Person]):
        """Initialize with shared person cache."""
        self._person_cache = person_cache
        # Services will be set by the handler
        self._llm_service = None
        self._diagram = None
        self._conversation_manager = None
        self._prompt_builder = None
        self._filesystem_adapter = None
        # Utility handlers
        self._prompt_resolver = None
        self._text_format_handler = TextFormatHandler()
        self._conversation_handler = ConversationHandler()
    
    def set_services(self, llm_service, diagram, conversation_manager, prompt_builder, filesystem_adapter=None):
        """Set services for the executor to use."""
        self._llm_service = llm_service
        self._diagram = diagram
        self._conversation_manager = conversation_manager
        self._prompt_builder = prompt_builder
        self._filesystem_adapter = filesystem_adapter
        # Initialize prompt resolver with filesystem and diagram
        self._prompt_resolver = PromptFileResolver(filesystem_adapter, diagram)
    
    async def execute(self, request: ExecutionRequest[PersonJobNode]) -> NodeOutputProtocol:
        """Execute the person job for a single person."""
        # Get node and context from request
        node = request.node
        context = request.context
        
        # Get inputs from request (already resolved by engine)
        inputs = request.inputs or {}
        
        # Direct typed access to person_id
        person_id = node.person

        # Use pre-configured services (set by handler)
        llm_service = self._llm_service
        execution_count = context.get_node_execution_count(node.id)
        logger.info(f"[EXECUTE_REQUEST] PersonJobNode {node.id} - execution_count: {execution_count}")

        # Create a fresh PromptFileResolver with the current diagram
        # This ensures we have the correct diagram_source_path metadata
        prompt_resolver_for_execution = PromptFileResolver(self._filesystem_adapter, self._diagram)

        # Get or create person
        person = self._get_or_create_person(person_id, self._conversation_manager)
        
        # Apply memory settings if configured
        # Note: We apply memory settings even on first execution because some nodes
        # (like judge panels) need to see full conversation history from the start
        memory_settings = None
        
        # Check if memory_profile is set (new way)
        if hasattr(node, 'memory_profile') and node.memory_profile:
            try:
                # Convert string to MemoryProfile enum
                profile_enum = MemoryProfile[node.memory_profile]
                if profile_enum != MemoryProfile.CUSTOM:
                    # Get settings from profile
                    memory_settings = MemoryProfileFactory.get_settings(profile_enum)
                else:
                    # Use custom memory_settings if profile is CUSTOM
                    memory_settings = node.memory_settings
            except (KeyError, AttributeError):
                logger.warning(f"Invalid memory profile: {node.memory_profile}")
                # Fall back to memory_settings
                memory_settings = node.memory_settings
        else:
            # Fall back to legacy memory_settings
            memory_settings = node.memory_settings
        
        if memory_settings:
            # Convert dict to MemorySettings object if needed
            if isinstance(memory_settings, dict):
                from dipeo.diagram_generated import MemorySettings as MemorySettingsModel
                memory_settings = MemorySettingsModel(**memory_settings)
                person.apply_memory_settings(memory_settings)
            else:
                person.apply_memory_settings(memory_settings)
        
        # Use inputs directly
        transformed_inputs = inputs
        
        # Handle conversation inputs
        has_conversation_input = self._conversation_handler.has_conversation_input(transformed_inputs)
        if has_conversation_input:
            self._conversation_handler.load_conversation_from_inputs(person, transformed_inputs)

        # Build prompt BEFORE applying memory management
        template_values = self._prompt_builder.prepare_template_values(
            transformed_inputs, 
            conversation_manager=self._conversation_manager,
            person_id=person_id
        )
        
        # Load prompts using the prompt resolver
        prompt_content = node.default_prompt
        first_only_content = node.first_only_prompt
        
        # Load first_prompt_file if specified (takes precedence over inline first_only_prompt)
        if hasattr(node, 'first_prompt_file') and node.first_prompt_file:
            loaded_content = prompt_resolver_for_execution.load_prompt_file(
                node.first_prompt_file,
                node.label or node.id
            )
            if loaded_content:
                first_only_content = loaded_content
        
        # Load prompt_file if specified (for default prompt)
        if hasattr(node, 'prompt_file') and node.prompt_file:
            loaded_content = prompt_resolver_for_execution.load_prompt_file(
                node.prompt_file,
                node.label or node.id
            )
            if loaded_content:
                prompt_content = loaded_content

        # Disable auto-prepend if we have conversation input (to avoid duplication)
        built_prompt = self._prompt_builder.build(
            prompt=prompt_content,
            first_only_prompt=first_only_content,
            execution_count=execution_count,
            template_values=template_values,
            auto_prepend_conversation=not has_conversation_input
        )
        
        # Log the built prompt
        if '{{' in (built_prompt or ''):
            logger.warning(f"[PersonJob {node.label or node.id}] Template variables may not be substituted! Found '{{{{' in built prompt")

        # Skip if no prompt
        if not built_prompt:
            logger.warning(f"Skipping execution for person {person_id} - no prompt available")
            return TextOutput(
                value="",
                node_id=node.id,
                metadata="{}"  # Empty metadata - skipped status handled by empty value
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
        
        # Handle tools configuration
        if hasattr(node, 'tools') and node.tools and node.tools != 'none':
            # Convert string tools value to ToolConfig array
            tools_config = []
            if node.tools == 'image':
                from dipeo.diagram_generated.domain_models import ToolConfig, ToolType
                tools_config.append(ToolConfig(
                    type=ToolType.IMAGE_GENERATION,
                    enabled=True
                ))
            elif node.tools == 'websearch':
                from dipeo.diagram_generated.domain_models import ToolConfig, ToolType
                tools_config.append(ToolConfig(
                    type=ToolType.WEB_SEARCH,
                    enabled=True
                ))
            
            if tools_config:
                complete_kwargs["tools"] = tools_config
        
        # Handle text_format configuration for structured outputs
        pydantic_model = self._text_format_handler.get_pydantic_model(node)
        if pydantic_model:
            complete_kwargs["text_format"] = pydantic_model
            
        result = await person.complete(**complete_kwargs)

        
        # Build and return output
        return self._build_node_output(
            result=result,
            person=person,
            node=node,
            diagram=self._diagram,
            model=person.llm_config.model
        )
    
    def _get_or_create_person(
        self,
        person_id: str,
        conversation_manager: Any
    ) -> Person:
        # Check cache first
        if person_id in self._person_cache:
            return self._person_cache[person_id]
        
        # Use the orchestrator's get_or_create_person method
        # which properly handles repository access and wiring
        if hasattr(conversation_manager, 'get_or_create_person'):
            from dipeo.diagram_generated import PersonID
            person = conversation_manager.get_or_create_person(
                person_id=PersonID(person_id),
                name=person_id  # Use person_id as default name
            )
        else:
            # Fallback for backward compatibility (should not happen with new architecture)
            from dipeo.diagram_generated import ApiKeyID, LLMService, PersonLLMConfig, PersonID
            person_config = PersonLLMConfig(
                service=LLMService.OPENAI,
                model="gpt-5-nano-2025-08-07",
                api_key_id=ApiKeyID("default")
            )
            
            person = Person(
                id=PersonID(person_id),
                name=person_id,
                llm_config=person_config,
                conversation_manager=conversation_manager
            )
        
        # Cache the person for this execution
        self._person_cache[person_id] = person
        
        return person
    
    
    
    def _build_node_output(self, result: Any, person: Person, node: PersonJobNode, diagram: Any, model: str) -> NodeOutputProtocol:
        from dipeo.diagram_generated import TokenUsage
        from dipeo.core.execution.node_output import TextOutput, DataOutput
        
        # Extract token usage as typed field
        token_usage = None
        if hasattr(result, 'token_usage') and result.token_usage:
            token_usage = TokenUsage(
                input=result.token_usage.input,
                output=result.token_usage.output,
                cached=result.token_usage.cached if hasattr(result.token_usage, 'cached') else None,
                total=result.token_usage.total if hasattr(result.token_usage, 'total') else None
            )
        
        # Get person and conversation IDs
        person_id = str(person.id) if person.id else None
        conversation_id = None  # Person doesn't directly store conversation_id
        
        # Check if conversation output is needed
        if self._conversation_handler.needs_conversation_output(str(node.id), diagram):
            # Return PersonJobOutput with messages
            messages = []
            for msg in person.get_messages():
                messages.append(msg)
            
            return PersonJobOutput(
                value=messages,
                node_id=node.id,
                metadata="{}",  # Empty metadata - model is now a typed field
                token_usage=token_usage,
                person_id=person_id,
                conversation_id=conversation_id,
                model=model  # Use typed field for model
            )
        else:
            # Check if we used text_format (structured output)
            has_text_format = (hasattr(node, 'text_format') and node.text_format) or \
                              (hasattr(node, 'text_format_file') and node.text_format_file)
            
            structured_data = self._text_format_handler.process_structured_output(result, has_text_format)
            if structured_data:
                return DataOutput(
                    value=structured_data,
                    node_id=node.id,
                    metadata="{}",
                    token_usage=token_usage,
                    execution_time=None,
                    retry_count=0
                )
            
            # Default: return text output
            return TextOutput(
                value=result.text if hasattr(result, 'text') else str(result),
                node_id=node.id,
                metadata="{}",
                token_usage=token_usage,
                execution_time=None,
                retry_count=0
            )