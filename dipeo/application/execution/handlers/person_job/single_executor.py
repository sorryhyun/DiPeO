"""Single person job executor - handles execution for a single person."""

import json
import logging
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.config.llm import PERSON_JOB_TEMPERATURE, PERSON_JOB_MAX_TOKENS
from dipeo.domain.conversation import Person
from dipeo.diagram_generated.generated_nodes import PersonJobNode
from dipeo.domain.execution.envelope import Envelope, EnvelopeFactory
from dipeo.diagram_generated.domain_models import Message, PersonID
from dipeo.application.execution.use_cases import PromptLoadingUseCase

from .text_format_handler import TextFormatHandler
from .conversation_handler import ConversationHandler

if TYPE_CHECKING:
    from dipeo.domain.execution.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


class SinglePersonJobExecutor:
    """Executor for single person job execution."""
    
    def __init__(self):
        """Initialize the executor."""
        # Services will be set by the handler
        self._llm_service = None
        self._diagram = None
        self._execution_orchestrator = None
        self._prompt_builder = None
        self._filesystem_adapter = None
        # Use cases
        self._prompt_loading_use_case = None
        # Utility handlers
        self._text_format_handler = TextFormatHandler()
        self._conversation_handler = ConversationHandler()
    
    def set_services(self, llm_service, diagram, execution_orchestrator, prompt_builder, filesystem_adapter=None):
        """Set services for the executor to use."""
        self._llm_service = llm_service
        self._diagram = diagram
        self._execution_orchestrator = execution_orchestrator
        self._prompt_builder = prompt_builder
        self._filesystem_adapter = filesystem_adapter
        # Initialize prompt loading use case with filesystem
        if filesystem_adapter:
            self._prompt_loading_use_case = PromptLoadingUseCase(filesystem_adapter)
    
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

        # Get or create person using the orchestrator directly
        if not self._execution_orchestrator:
            raise ValueError(f"ExecutionOrchestrator not available for person {person_id}")
        
        person = self._execution_orchestrator.get_or_create_person(
            PersonID(person_id),
            diagram=self._diagram
        )
        
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
            if messages_to_add and hasattr(self._execution_orchestrator, 'add_message'):
                for msg in messages_to_add:
                    self._execution_orchestrator.add_message(
                        msg,
                        execution_id=trace_id,
                        node_id=str(node.id)
                    )

        # Get all messages from conversation repository via orchestrator
        all_messages = self._execution_orchestrator.get_conversation().messages if hasattr(self._execution_orchestrator, 'get_conversation') else []
        
        # Load prompts early to use for task_prompt_preview
        prompt_content = node.default_prompt
        first_only_content = node.first_only_prompt
        
        # Check for pre-resolved prompts from compile-time (preferred)
        if hasattr(node, 'resolved_first_prompt') and node.resolved_first_prompt:
            # Use pre-resolved content from compilation
            first_only_content = node.resolved_first_prompt
            logger.debug(f"[PersonJob {node.label or node.id}] Using pre-resolved first prompt")
        elif hasattr(node, 'first_prompt_file') and node.first_prompt_file and self._prompt_loading_use_case:
            # Fall back to runtime loading if not pre-resolved
            diagram_source_path = self._prompt_loading_use_case.get_diagram_source_path(self._diagram)
            loaded_content = self._prompt_loading_use_case.load_prompt_file(
                node.first_prompt_file,
                diagram_source_path,
                node.label or node.id
            )
            if loaded_content:
                first_only_content = loaded_content
        
        # Check for pre-resolved default prompt
        if hasattr(node, 'resolved_prompt') and node.resolved_prompt:
            # Use pre-resolved content from compilation
            prompt_content = node.resolved_prompt
            logger.debug(f"[PersonJob {node.label or node.id}] Using pre-resolved default prompt")
        elif hasattr(node, 'prompt_file') and node.prompt_file and self._prompt_loading_use_case:
            # Fall back to runtime loading if not pre-resolved
            diagram_source_path = self._prompt_loading_use_case.get_diagram_source_path(self._diagram)
            loaded_content = self._prompt_loading_use_case.load_prompt_file(
                node.prompt_file,
                diagram_source_path,
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
        
        # Apply memory settings through the person's brain if available
        if memorize_to or at_most:
            # Build task preview with template substitution
            task_preview_raw = prompt_content or first_only_content or ""
            task_preview = self._prompt_builder.build(
                prompt=task_preview_raw,
                template_values=template_values,
                first_only_prompt=None,
                execution_count=execution_count
            )
            
            # Use the Person's brain for memory selection
            # The brain is now properly wired with a memory selector
            selected_result = await person.select_memories(
                candidate_messages=all_messages,
                prompt_preview=task_preview,
                memorize_to=memorize_to,
                at_most=at_most,
                llm_service=self._llm_service,
            )
            # Brain returns None if no criteria, or list of messages
            filtered_messages = selected_result if selected_result is not None else person.get_messages(all_messages)
            
            # Special handling for GOLDFISH mode - clear conversation for this person
            if memorize_to and memorize_to.strip().upper() == "GOLDFISH":
                if hasattr(self._execution_orchestrator, 'clear_person_messages'):
                    self._execution_orchestrator.clear_person_messages(person.id)
                person.reset_memory()
        else:
            # Default behavior - use person's standard filtering through get_messages
            filtered_messages = person.get_messages(all_messages)
        
        # Update conversation context with filtered messages
        conversation_context = person.get_conversation_context(filtered_messages)
        
        # Extract and parse JSON content from selected memories for template use
        memory_data = {}
        if filtered_messages:
            for msg in filtered_messages:
                # Try to parse JSON content from messages
                if msg.content:
                    try:
                        parsed_content = json.loads(msg.content)
                        # Merge parsed content into memory_data
                        if isinstance(parsed_content, dict):
                            memory_data.update(parsed_content)
                            logger.debug(f"[PersonJob] Extracted memory data keys: {list(parsed_content.keys())}")
                    except (json.JSONDecodeError, TypeError):
                        # Not JSON or not parseable, skip - this is expected for most messages
                        pass
        
        if memory_data:
            logger.info(f"[PersonJob] Successfully extracted memory data with keys: {list(memory_data.keys())}")
        
        # Update template values with the filtered conversation context and memory data
        template_values = {
            **input_values,
            **conversation_context,
            **memory_data  # Add parsed memory content
        }
        
        # Re-merge global variables to ensure they're still available
        template_values = {**variables, **template_values}
        
        
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
            "temperature": PERSON_JOB_TEMPERATURE,
            "max_tokens": PERSON_JOB_MAX_TOKENS,
            "execution_phase": "direct_execution",  # Set phase for Claude Code adapter
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
        
        # Use the simplified Person.complete() directly
        result, incoming_msg, response_msg = await person.complete(
            all_messages=messages_for_completion,
            **complete_kwargs
        )
        
        # Add messages to conversation via orchestrator
        if hasattr(self._execution_orchestrator, 'add_message'):
            # Add incoming message
            self._execution_orchestrator.add_message(
                incoming_msg,
                execution_id=trace_id,
                node_id=str(node.id)
            )
            # Add response message
            self._execution_orchestrator.add_message(
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
    
    
    
    def _build_node_output(self, result: Any, person: Person, node: PersonJobNode, diagram: Any, model: str, trace_id: str = "", selected_messages: Optional[list] = None) -> Envelope:
        """Build node output with envelope support for proper conversion."""
        from dipeo.diagram_generated import TokenUsage
        
        # Extract token usage as typed field
        token_usage = None
        if hasattr(result, 'token_usage') and result.token_usage:
            token_usage = TokenUsage(
                input=result.token_usage.input_tokens,
                output=result.token_usage.output_tokens,
                cached=result.token_usage.cached if hasattr(result.token_usage, 'cached') else None,
                total=result.token_usage.total_tokens if hasattr(result.token_usage, 'total_tokens') else None
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
                all_conv_messages = self._execution_orchestrator.get_conversation().messages if hasattr(self._execution_orchestrator, 'get_conversation') else []
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