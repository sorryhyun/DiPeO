# Unified prompt building service

import logging
import warnings
from typing import Any

from dipeo.utils.template import TemplateProcessor

logger = logging.getLogger(__name__)


class PromptBuilder:
    
    def __init__(self, template_processor: TemplateProcessor | None = None):
        self._processor = template_processor or TemplateProcessor()
    
    def build(
        self,
        prompt: str,
        first_only_prompt: str | None = None,
        execution_count: int = 0,
        template_values: dict[str, Any] | None = None,
        raw_inputs: dict[str, Any] | None = None,
        auto_prepend_conversation: bool = True,
    ) -> str:
        selected_prompt = self._select_prompt(prompt, first_only_prompt, execution_count)
        
        if template_values is None:
            if raw_inputs is None:
                template_values = {}
            else:
                template_values = self.prepare_template_values(raw_inputs)
        
        # Check if auto-prepend is enabled via parameter or settings
        should_prepend = auto_prepend_conversation
        # If explicitly False, respect that. Otherwise check settings.
        if auto_prepend_conversation is not False:
            try:
                from dipeo.infra.config.settings import get_settings
                should_prepend = get_settings().auto_prepend_conversation
            except:
                pass  # Keep default True if settings not available
        
        # Auto-prepend conversation if enabled and available
        if should_prepend and template_values:
            selected_prompt = self._prepend_conversation_context(selected_prompt, template_values)
        
        # Use full template processing to support Handlebars syntax
        result = self._processor.process(selected_prompt, template_values)
        if result.errors:
            logger.warning(f"Template processing errors: {result.errors}")
        return result.content
    
    def prepare_template_values(self, inputs: dict[str, Any], conversation_manager=None, person_id=None) -> dict[str, Any]:

        # Use inputs directly - no unwrapping needed
        unwrapped_inputs = inputs
        template_values = {}
        
        # Add global conversation if manager is available
        if conversation_manager:
            global_conversation = conversation_manager.get_conversation()
            if global_conversation:
                messages = global_conversation.messages
                template_values['global_conversation'] = [
                    {
                        'from': str(msg.from_person_id) if msg.from_person_id else '',
                        'to': str(msg.to_person_id) if msg.to_person_id else '',
                        'content': msg.content,
                        'type': msg.message_type
                    } for msg in messages
                ]
                template_values['global_message_count'] = len(messages)
                
                # Also add person-specific conversations
                person_conversations = {}
                for msg in messages:
                    # Add to sender's view
                    if msg.from_person_id != "system":
                        if msg.from_person_id not in person_conversations:
                            person_conversations[msg.from_person_id] = []
                        person_conversations[msg.from_person_id].append({
                            'role': 'assistant',
                            'content': msg.content
                        })
                    
                    # Add to recipient's view
                    if msg.to_person_id != "system":
                        if msg.to_person_id not in person_conversations:
                            person_conversations[msg.to_person_id] = []
                        person_conversations[msg.to_person_id].append({
                            'role': 'user',
                            'content': msg.content
                        })
                
                template_values['person_conversations'] = person_conversations
        
        for key, value in unwrapped_inputs.items():
            if isinstance(value, (str, int, float, bool, type(None))):
                template_values[key] = value
            
            elif isinstance(value, dict):
                if "messages" in value:
                    # Extract the last message content as the argument to respond to
                    messages = value.get("messages", [])
                    if messages:
                        # Convert Message objects to dicts if needed
                        messages_as_dicts = []
                        for msg in messages:
                            if hasattr(msg, 'model_dump'):
                                # Pydantic model - convert to dict
                                messages_as_dicts.append(msg.model_dump())
                            elif hasattr(msg, '__dict__'):
                                # Regular object - convert attributes to dict
                                messages_as_dicts.append({
                                    'from_person_id': str(getattr(msg, 'from_person_id', '')),
                                    'to_person_id': str(getattr(msg, 'to_person_id', '')),
                                    'content': getattr(msg, 'content', ''),
                                    'message_type': getattr(msg, 'message_type', ''),
                                    'timestamp': getattr(msg, 'timestamp', '')
                                })
                            elif isinstance(msg, dict):
                                # Already a dict
                                messages_as_dicts.append(msg)
                        
                        # Get the last message content
                        last_message = messages_as_dicts[-1] if messages_as_dicts else None
                        if last_message and "content" in last_message:
                            template_values[f"{key}_last_message"] = last_message["content"]
                            # Also make the full conversation available
                            template_values[f"{key}_messages"] = messages_as_dicts
                            
                        import logging
                        logger = logging.getLogger(__name__)
                        logger.debug(f"Prepared {key}_messages with {len(messages_as_dicts)} messages")
                    continue
                    
                if "value" in value and isinstance(value["value"], dict) and "default" in value["value"]:
                    template_values[key] = value["value"]["default"]
                elif all(isinstance(v, (str, int, float, bool, type(None))) for v in value.values()):
                    template_values[key] = value
            
            elif isinstance(value, list) and all(isinstance(v, (str, int, float, bool)) for v in value):
                template_values[key] = value
        

        return template_values
    
    def should_use_first_only_prompt(
        self,
        first_only_prompt: str | None,
        execution_count: int
    ) -> bool:
        # execution_count is 1 on first run because it's incremented before execution
        return bool(first_only_prompt and execution_count == 1)
    
    def _select_prompt(
        self,
        default_prompt: str,
        first_only_prompt: str | None,
        execution_count: int,
    ) -> str:
        # Debug logging

        if self.should_use_first_only_prompt(first_only_prompt, execution_count):
            return first_only_prompt
        return default_prompt
    
    def build_with_context(
        self,
        prompt: str,
        context: dict[str, Any],
        first_only_prompt: str | None = None,
        execution_count: int = 0,
    ) -> str:
        selected_prompt = self._select_prompt(prompt, first_only_prompt, execution_count)
        result = self._processor.process(selected_prompt, context)
        
        if result.errors:
            for error in result.errors:
                warnings.warn(f"Template processing error: {error}", UserWarning)
        
        if result.missing_keys:
            warnings.warn(
                f"Missing template keys: {', '.join(result.missing_keys)}",
                UserWarning
            )
        
        return result.content
    
    def _prepend_conversation_context(self, prompt: str, template_values: dict[str, Any]) -> str:
        # Check if conversation data is available
        if 'global_conversation' not in template_values:
            return prompt
        
        # Check if prompt already references conversation variables
        conversation_vars = ['global_conversation', 'global_message_count', 'person_conversations']
        if any(f'{{{{{var}' in prompt or f'{{#{var}' in prompt for var in conversation_vars):
            # Prompt already uses conversation variables, don't prepend
            return prompt
        
        # Check if conversation input is already provided (e.g., from conversation_state edges)
        # This avoids double-prepending when conversation is passed as input
        has_conversation_input = any(
            key.endswith('_messages') and isinstance(value, list) 
            for key, value in template_values.items()
        )
        if has_conversation_input:
            # Log which keys triggered this
            conv_keys = [k for k, v in template_values.items() if k.endswith('_messages') and isinstance(v, list)]
            return prompt
        
        # Check if the prompt or any conversation messages already contain "[Previous conversation"
        # This prevents nested repetition when conversations are passed through loops
        global_conversation = template_values.get('global_conversation', [])
        for msg in global_conversation:
            content = msg.get('content', '')
            if '[Previous conversation' in content:
                return prompt
        
        # Check if there are any messages to prepend
        global_conversation = template_values.get('global_conversation', [])
        if not global_conversation:
            return prompt
        
        # Get context limit from settings
        try:
            from dipeo.infra.config.settings import get_settings
            context_limit = get_settings().conversation_context_limit
        except:
            context_limit = 10  # Default fallback
        
        # Build conversation context
        conversation_context = []
        conversation_context.append(f"[Previous conversation with {len(global_conversation)} messages]")
        
        # Include recent messages (limit to configured amount for context)
        recent_messages = global_conversation[-context_limit:] if len(global_conversation) > context_limit else global_conversation
        
        for msg in recent_messages:
            from_person = msg.get('from', 'unknown')
            content = msg.get('content', '')
            if content:  # Only include non-empty messages
                conversation_context.append(f"{from_person}: {content}")
        
        if len(global_conversation) > context_limit:
            conversation_context.append(f"... ({len(global_conversation) - context_limit} earlier messages omitted)")
        
        conversation_context.append("")  # Empty line separator
        
        # Prepend to prompt
        conversation_text = "\n".join(conversation_context)
        return f"{conversation_text}\n{prompt}"