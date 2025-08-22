"""Single person job executor - handles execution for a single person."""

import json
import logging
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.domain.conversation import Person
from dipeo.diagram_generated.generated_nodes import PersonJobNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.domain_models import Message, PersonID

from .prompt_resolver import PromptFileResolver
from .text_format_handler import TextFormatHandler
from .conversation_handler import ConversationHandler

if TYPE_CHECKING:
    from dipeo.domain.execution.execution_context import ExecutionContext

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
    
    async def execute(self, request: ExecutionRequest[PersonJobNode]) -> Envelope:
        """Execute the person job for a single person with envelope support.
        
        Returns Envelope that contains the execution results.
        """
        # Get node and context from request
        node = request.node
        context = request.context
        trace_id = request.execution_id or ""
        
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
        
        # Use inputs directly
        transformed_inputs = inputs
        
        # Handle conversation inputs
        has_conversation_input = self._conversation_handler.has_conversation_input(transformed_inputs)
        if has_conversation_input:
            # Get messages to be added from inputs
            messages_to_add = self._conversation_handler.load_conversation_from_inputs(
                transformed_inputs, str(person.id)
            )
            # Add messages via orchestrator
            if messages_to_add and hasattr(self._conversation_manager, 'add_message'):
                for msg in messages_to_add:
                    self._conversation_manager.add_message(
                        msg,
                        execution_id=trace_id,
                        node_id=str(node.id)
                    )

        # Get all messages from conversation repository via orchestrator
        all_messages = self._conversation_manager.get_conversation().messages if hasattr(self._conversation_manager, 'get_conversation') else []
        
        # Load prompts early to use for task_prompt_preview
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
        
        # Handle memorize_to feature - unified memory management
        memorize_to = getattr(node, "memorize_to", None)
        at_most = getattr(node, "at_most", None)
        
        # Prepare template values early for task preview
        input_values = self._prompt_builder.prepare_template_values(transformed_inputs)
        logger.debug(f"[PersonJob] input_values keys after prepare: {list(input_values.keys())}")
        
        # Get conversation context with all messages first (will be filtered later)
        conversation_context = person.get_conversation_context(all_messages)
        
        # Combine input values with conversation context
        template_values = {
            **input_values,
            **conversation_context
        }
        
        # Merge global variables from context to make them available in templates
        variables = context.get_variables() if hasattr(context, "get_variables") else {}
        template_values = {**variables, **template_values}
        
        # Apply memory settings through the unified selector
        if memorize_to or at_most:
            # Get the memory selector from orchestrator
            memory_selector = getattr(self._conversation_manager, '_memory_selector', None)
            if not memory_selector:
                from .memory_selector import MemorySelector
                memory_selector = MemorySelector(self._conversation_manager)
            
            # Build task preview with template substitution
            task_preview_raw = prompt_content or first_only_content or ""
            task_preview = self._prompt_builder.build(
                prompt=task_preview_raw,
                template_values=template_values,
                first_only_prompt=None,
                execution_count=execution_count
            )
            
            # Apply memory settings to get filtered messages
            filtered_messages = await memory_selector.apply_memory_settings(
                person=person,
                all_messages=all_messages,
                memorize_to=memorize_to,
                at_most=at_most,
                task_prompt_preview=task_preview,
                llm_service=self._llm_service,
            )
            
            # Special handling for GOLDFISH mode - clear conversation for this person
            if memorize_to and memorize_to.strip().upper() == "GOLDFISH":
                if hasattr(self._conversation_manager, 'clear_person_messages'):
                    self._conversation_manager.clear_person_messages(person.id)
                person.reset_memory()
        else:
            # Default behavior - use person's standard filtering
            filtered_messages = person.filter_messages(all_messages)
        
        # Update conversation context with filtered messages
        conversation_context = person.get_conversation_context(filtered_messages)
        
        # Update template values with the filtered conversation context
        template_values = {
            **input_values,
            **conversation_context
        }
        
        # Re-merge global variables to ensure they're still available
        template_values = {**variables, **template_values}
        
        logger.debug(f"[PersonJob] final template_values keys: {list(template_values.keys())}")
        
        # Build prompt with template substitution (prompts already loaded earlier)
        built_prompt = self._prompt_builder.build(
            prompt=prompt_content,
            template_values=template_values,
            first_only_prompt=first_only_content,
            execution_count=execution_count
        )
        
        # Prepend conversation if appropriate (not for GOLDFISH or when conversation is already provided)
        # if not has_conversation_input and not is_goldfish:
        #     built_prompt = self._prompt_builder.prepend_conversation_if_needed(
        #         built_prompt,
        #         conversation_context
        #     )
        
        # Log the built prompt
        if '{{' in (built_prompt or ''):
            logger.warning(f"[PersonJob {node.label or node.id}] Template variables may not be substituted! Found '{{{{' in built prompt")

        # Skip if no prompt
        if not built_prompt:
            logger.warning(f"Skipping execution for person {person_id} - no prompt available")
            logger.warning(f"prompt_content: {prompt_content}, first_only_content: {first_only_content}")
            logger.warning(f"node.prompt_file: {getattr(node, 'prompt_file', None)}")
            logger.warning(f"filesystem_adapter: {self._filesystem_adapter}")
            return EnvelopeFactory.text(
                "",
                produced_by=str(node.id),
                trace_id=trace_id
            )
        
        # Execute LLM call
        # Only pass tools if they are configured
        complete_kwargs = {
            "prompt": built_prompt,
            "llm_service": llm_service,
            "from_person_id": "system",
            "temperature": 0.2,
            "max_tokens": 128000,
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
            
        # Use filtered messages for completion
        messages_for_completion = filtered_messages
        
        # Check if orchestrator has the new helper method
        if hasattr(self._conversation_manager, 'execute_person_completion'):
            # Pass the filtered messages for completion
            complete_kwargs['all_messages'] = messages_for_completion
            result = await self._conversation_manager.execute_person_completion(
                person=person,
                execution_id=trace_id,
                node_id=str(node.id),
                **complete_kwargs
            )
        else:
            # Fallback: handle the new Person API directly
            result, incoming_msg, response_msg = await person.complete(
                all_messages=messages_for_completion,
                **complete_kwargs
            )
            
            # Add messages to conversation via orchestrator
            if hasattr(self._conversation_manager, 'add_message'):
                # Add incoming message
                self._conversation_manager.add_message(
                    incoming_msg,
                    execution_id=trace_id,
                    node_id=str(node.id)
                )
                # Add response message
                self._conversation_manager.add_message(
                    response_msg,
                    execution_id=trace_id,
                    node_id=str(node.id)
                )

        
        # Build and return output with envelope support
        return self._build_node_output(
            result=result,
            person=person,
            node=node,
            diagram=self._diagram,
            model=person.llm_config.model,
            trace_id=trace_id,
            selected_messages=filtered_messages
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
    
    
    
    def _build_node_output(self, result: Any, person: Person, node: PersonJobNode, diagram: Any, model: str, trace_id: str = "", selected_messages: Optional[list] = None) -> Envelope:
        """Build node output with envelope support for proper conversion."""
        from dipeo.diagram_generated import TokenUsage
        
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
            # If memorize_to was used, return the selected subset
            if selected_messages is not None:
                messages = selected_messages
            else:
                # Get all messages from conversation repository
                all_conv_messages = self._conversation_manager.get_conversation().messages if hasattr(self._conversation_manager, 'get_conversation') else []
                # Filter messages from person's perspective
                messages = person.get_messages(all_conv_messages)
            
            # Return conversation envelope directly
            conversation_state = {
                "messages": messages,
                "last_message": messages[-1] if messages else None
            }
            return EnvelopeFactory.conversation(
                conversation_state,
                produced_by=str(node.id),
                trace_id=trace_id
            ).with_meta(
                person_id=person_id,
                conversation_id=conversation_id,
                model=model,
                token_usage=token_usage.model_dump() if token_usage else None
            )
        else:
            # Check if we used text_format (structured output)
            has_text_format = (hasattr(node, 'text_format') and node.text_format) or \
                              (hasattr(node, 'text_format_file') and node.text_format_file)
            
            structured_data = self._text_format_handler.process_structured_output(result, has_text_format)
            if structured_data:
                # Return JSON envelope for structured data
                return EnvelopeFactory.json(
                    structured_data,
                    produced_by=str(node.id),
                    trace_id=trace_id
                ).with_meta(
                    person_id=person_id,
                    model=model,
                    is_structured=True,
                    token_usage=token_usage.model_dump() if token_usage else None
                )
            
            # Default: return text output
            text_value = result.text if hasattr(result, 'text') else str(result)
            output = EnvelopeFactory.text(
                text_value,
                produced_by=str(node.id),
                trace_id=trace_id
            ).with_meta(
                person_id=person_id,
                model=model,
                token_usage=token_usage.model_dump() if token_usage else None
            )
            
            return output