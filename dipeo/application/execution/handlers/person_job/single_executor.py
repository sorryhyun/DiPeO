"""Single person job executor - handles execution for a single person."""

import logging
from typing import TYPE_CHECKING, Any, Optional

from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.registry import (
    LLM_SERVICE,
    DIAGRAM,
    CONVERSATION_MANAGER,
    PROMPT_BUILDER
)
from dipeo.domain.conversation import Person
from dipeo.domain.conversation.memory_profiles import MemoryProfile, MemoryProfileFactory
from dipeo.diagram_generated.generated_nodes import PersonJobNode
from dipeo.core.execution.node_output import ConversationOutput, TextOutput, NodeOutputProtocol
from dipeo.diagram_generated.domain_models import Message, PersonID

if TYPE_CHECKING:
    from dipeo.core.execution.execution_context import ExecutionContext

logger = logging.getLogger(__name__)


class SinglePersonJobExecutor:
    """Executor for single person job execution."""
    
    def __init__(self, person_cache: dict[str, Person]):
        """Initialize with shared person cache."""
        self._person_cache = person_cache
    
    async def execute(self, request: ExecutionRequest[PersonJobNode]) -> NodeOutputProtocol:
        """Execute the person job for a single person."""
        # Get node and context from request
        node = request.node
        context = request.context
        
        # Get inputs from request (already resolved by engine)
        inputs = request.inputs or {}
        
        # Direct typed access to person_id
        person_id = node.person

        # Get services using request helper methods
        llm_service = request.get_service(LLM_SERVICE.name)
        diagram = request.get_service(DIAGRAM.name)
        conversation_manager = request.get_service(CONVERSATION_MANAGER.name)
        prompt_builder = request.get_service(PROMPT_BUILDER.name)
        
        if not all([llm_service, diagram, conversation_manager, prompt_builder]):
            raise ValueError("Required services not available")
        

        execution_count = context.get_node_execution_count(node.id)

        # Get or create person
        person = self._get_or_create_person(person_id, conversation_manager)
        
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
        has_conversation_input = self._has_conversation_input(transformed_inputs)
        if has_conversation_input:
            self._rebuild_conversation(person, transformed_inputs)

        # Build prompt BEFORE applying memory management
        logger.info(f"[PersonJob {node.label or node.id}] Raw inputs: {list(request.inputs.keys())}")
        logger.info(f"[PersonJob {node.label or node.id}] Transformed inputs: {list(transformed_inputs.keys())}")
        logger.debug(f"[PersonJob {node.label or node.id}] Transformed inputs detail: {transformed_inputs}")
        
        template_values = prompt_builder.prepare_template_values(
            transformed_inputs, 
            conversation_manager=conversation_manager,
            person_id=person_id
        )
        
        # Log template values for debugging
        logger.info(f"[PersonJob {node.label or node.id}] Template values: {list(template_values.keys())}")
        logger.debug(f"[PersonJob {node.label or node.id}] Template values detail: {template_values}")
        
        # Check if prompt_file is specified and load the prompt from file
        prompt_content = node.default_prompt
        first_only_content = node.first_only_prompt
        
        # Load first_prompt_file if specified (takes precedence over inline first_only_prompt)
        if hasattr(node, 'first_prompt_file') and node.first_prompt_file:
            filesystem = request.get_service("filesystem_adapter")
            if filesystem:
                try:
                    # Construct path to first prompt file
                    import os
                    from pathlib import Path
                    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                    first_prompt_path = Path(base_dir) / 'files' / 'prompts' / node.first_prompt_file
                    
                    # Read the first prompt file content
                    if filesystem.exists(first_prompt_path):
                        with filesystem.open(first_prompt_path, 'rb') as f:
                            file_content = f.read().decode('utf-8')
                            # Use file content as first only prompt
                            first_only_content = file_content
                            logger.info(f"[PersonJob {node.label or node.id}] Loaded first prompt from file: {node.first_prompt_file} ({len(file_content)} chars)")
                            logger.debug(f"[PersonJob {node.label or node.id}] First prompt content preview: {file_content[:200]}...")
                    else:
                        logger.warning(f"[PersonJob {node.label or node.id}] First prompt file not found: {node.first_prompt_file}")
                except Exception as e:
                    logger.error(f"Error loading first prompt file {node.first_prompt_file}: {e}")
        
        # Load prompt_file if specified (for default prompt)
        if hasattr(node, 'prompt_file') and node.prompt_file:
            filesystem = request.get_service("filesystem_adapter")
            if filesystem:
                try:
                    # Construct path to prompt file
                    import os
                    from pathlib import Path
                    base_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
                    prompt_path = Path(base_dir) / 'files' / 'prompts' / node.prompt_file
                    
                    # Read the prompt file content
                    if filesystem.exists(prompt_path):
                        with filesystem.open(prompt_path, 'rb') as f:
                            file_content = f.read().decode('utf-8')
                            # Use file content as default prompt
                            prompt_content = file_content
                            logger.info(f"[PersonJob {node.label or node.id}] Loaded prompt from file: {node.prompt_file} ({len(file_content)} chars)")
                            logger.debug(f"[PersonJob {node.label or node.id}] Prompt content preview: {file_content[:200]}...")
                    else:
                        logger.warning(f"[PersonJob {node.label or node.id}] Prompt file not found: {node.prompt_file}")
                except Exception as e:
                    logger.error(f"Error loading prompt file {node.prompt_file}: {e}")

        # Log the prompt before building
        logger.debug(f"[PersonJob {node.label or node.id}] Prompt before building: {prompt_content[:200] if prompt_content else 'None'}...")
        
        # Disable auto-prepend if we have conversation input (to avoid duplication)
        built_prompt = prompt_builder.build(
            prompt=prompt_content,
            first_only_prompt=first_only_content,
            execution_count=execution_count,
            template_values=template_values,
            auto_prepend_conversation=not has_conversation_input
        )
        
        # Log the built prompt
        logger.debug(f"[PersonJob {node.label or node.id}] Built prompt preview: {built_prompt[:200] if built_prompt else 'None'}...")
        if '{{' in (built_prompt or ''):
            logger.warning(f"[PersonJob {node.label or node.id}] Template variables may not be substituted! Found '{{{{' in built prompt")

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
        # First check for text_format_file (external file takes precedence)
        text_format_content = None
        
        if hasattr(node, 'text_format_file') and node.text_format_file:
            # Load Pydantic models from external file
            import os
            file_path = node.text_format_file
            
            # Handle relative paths from project root
            if not os.path.isabs(file_path):
                project_root = os.environ.get('DIPEO_BASE_DIR', os.getcwd())
                file_path = os.path.join(project_root, file_path)
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r') as f:
                        text_format_content = f.read()
                    logger.debug(f"Loaded text_format from file: {node.text_format_file}")
                except Exception as e:
                    logger.error(f"Failed to read text_format_file {node.text_format_file}: {e}")
            else:
                logger.warning(f"text_format_file not found: {node.text_format_file}")
        
        # Fall back to inline text_format if no file or file failed
        if not text_format_content and hasattr(node, 'text_format') and node.text_format:
            text_format_content = node.text_format
        
        # Process the text_format content if we have any
        if text_format_content:
            from dipeo.application.utils.pydantic_compiler import compile_pydantic_model, is_pydantic_code
            
            # Check if it's Python code string that defines Pydantic models
            if isinstance(text_format_content, str) and is_pydantic_code(text_format_content):
                # Compile the Python code into a Pydantic BaseModel class
                pydantic_model = compile_pydantic_model(text_format_content)
                if pydantic_model:
                    complete_kwargs["text_format"] = pydantic_model
                else:
                    logger.warning(f"Failed to compile Pydantic model from text_format")
            else:
                # If it's not Python code, log a warning (we no longer support JSON schema)
                logger.warning(f"text_format must be Python code defining Pydantic models")
            
        result = await person.complete(**complete_kwargs)

        
        # Build and return output
        return self._build_node_output(
            result=result,
            person=person,
            node=node,
            diagram=diagram,
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
        
        # Get person config from conversation manager
        person_config = None
        person_name = person_id  # Default to person_id as name
        
        if hasattr(conversation_manager, 'get_person_config'):
            person_config = conversation_manager.get_person_config(person_id)
        
        
        if not person_config:
            # Fallback: create minimal config with default LLM
            from dipeo.diagram_generated import ApiKeyID, LLMService, PersonLLMConfig
            person_config = PersonLLMConfig(
                service=LLMService.OPENAI,
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
        
        # Include token usage if available
        if hasattr(result, 'token_usage') and result.token_usage:
            metadata['token_usage'] = {
                'input': result.token_usage.input,
                'output': result.token_usage.output,
                'cached': result.token_usage.cached,
                'total': result.token_usage.total
            }
        
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