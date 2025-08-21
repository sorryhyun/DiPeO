# Unified prompt building service

import logging
import warnings
from typing import Any

from dipeo.domain.diagram.ports import TemplateProcessorPort

logger = logging.getLogger(__name__)


class PromptBuilder:
    
    def __init__(self, template_processor: TemplateProcessorPort | None = None):
        self._processor = template_processor
    
    def build(
        self,
        prompt: str,
        template_values: dict[str, Any],
        first_only_prompt: str | None = None,
        execution_count: int = 0,
    ) -> str:
        """Build a prompt with template substitution.
        
        This is now a pure template processor - conversation context
        should be provided in template_values from the domain layer.
        """
        selected_prompt = self._select_prompt(prompt, first_only_prompt, execution_count)
        
        # Handle None prompt - return empty string
        if selected_prompt is None:
            logger.warning("No prompt provided to PromptBuilder - returning empty string")
            return ""
        
        logger.debug(f"[PromptBuilder] template_values keys: {list(template_values.keys())}")
        if 'current_index' in template_values:
            logger.debug(f"[PromptBuilder] current_index: {template_values['current_index']}")
        if 'sections' in template_values:
            logger.debug(f"[PromptBuilder] sections type: {type(template_values['sections'])}, len: {len(template_values['sections']) if isinstance(template_values['sections'], list) else 'N/A'}")
        
        # Use template processing to support variable substitution
        if self._processor:
            result = self._processor.process(selected_prompt, template_values)
            if result.errors:
                logger.warning(f"Template processing errors: {result.errors}")
            if result.missing_keys:
                logger.warning(f"Template missing keys: {result.missing_keys}")
            return result.content
        else:
            # Return raw prompt if no processor available
            logger.warning("No template processor available!")
            return selected_prompt
    
    def prepare_template_values(self, inputs: dict[str, Any]) -> dict[str, Any]:
        """Prepare template values from inputs.
        
        This now only handles input transformation, not conversation context.
        Conversation context should be obtained from Person.get_conversation_context().
        """
        template_values = {}
        
        # Special handling for 'default' and 'first' inputs - flatten their properties to root context
        # This allows templates to access {{property}} instead of {{default.property}} or {{first.property}}
        for special_key in ['default', 'first']:
            if special_key in inputs and isinstance(inputs[special_key], dict):
                special_value = inputs[special_key]
                
                # Add all properties from the special input to the root context
                for prop_key, prop_value in special_value.items():
                    if prop_key not in template_values:  # Don't overwrite existing values
                        template_values[prop_key] = prop_value
                # Also keep the special object itself for backward compatibility
                template_values[special_key] = special_value
        
        # Process remaining inputs (skip already processed special keys)
        for key, value in inputs.items():
            if key in ['default', 'first']:
                continue  # Already processed above
            if isinstance(value, (str, int, float, bool, type(None))):
                template_values[key] = value
            
            elif isinstance(value, dict):
                if "messages" in value:
                    # Handle conversation data
                    messages = value.get("messages", [])
                    if messages:
                        # Convert to simple dicts
                        messages_as_dicts = []
                        for msg in messages:
                            if hasattr(msg, 'model_dump'):
                                messages_as_dicts.append(msg.model_dump())
                            elif isinstance(msg, dict):
                                messages_as_dicts.append(msg)
                            else:
                                # Convert object to dict
                                messages_as_dicts.append({
                                    'content': getattr(msg, 'content', ''),
                                    'from_person_id': str(getattr(msg, 'from_person_id', '')),
                                    'to_person_id': str(getattr(msg, 'to_person_id', ''))
                                })
                        
                        # Make last message and full conversation available
                        if messages_as_dicts:
                            last_msg = messages_as_dicts[-1]
                            if "content" in last_msg:
                                template_values[f"{key}_last_message"] = last_msg["content"]
                            template_values[f"{key}_messages"] = messages_as_dicts
                    continue
                    
                # For any dict value, make it available for dot notation access
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
        
        # Handle None prompt - return empty string
        if selected_prompt is None:
            logger.warning("No prompt provided to build_with_context - returning empty string")
            return ""
            
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
    
    def prepend_conversation_if_needed(self, prompt: str, conversation_context: dict[str, Any]) -> str:
        """Prepend conversation context to prompt if appropriate.
        
        This is now a simple utility that checks if the prompt already references
        conversation variables and prepends a summary if not.
        """
        # Check if prompt is None
        if prompt is None:
            return prompt
        
        # Check if conversation data is available
        if 'global_conversation' not in conversation_context:
            return prompt
        
        # Check if prompt already references conversation variables
        conversation_vars = ['global_conversation', 'global_message_count', 'person_conversations']
        if any(f'{{{{{var}' in prompt or f'{{#{var}' in prompt for var in conversation_vars):
            # Prompt already uses conversation variables, don't prepend
            return prompt
        
        # Check if there are any messages to prepend
        global_conversation = conversation_context.get('global_conversation', [])
        if not global_conversation:
            return prompt
        
        # Get context limit from settings
        try:
            from dipeo.config import get_settings
            settings = get_settings()
            # Get conversation context limit from settings (use a reasonable default)
            context_limit = getattr(settings, 'conversation_context_limit', 10)
        except:
            context_limit = 10  # Default fallback
        
        # Build conversation summary
        conversation_summary = []
        conversation_summary.append(f"[Previous conversation with {len(global_conversation)} messages]")
        
        # Include recent messages
        recent_messages = global_conversation[-context_limit:] if len(global_conversation) > context_limit else global_conversation
        
        for msg in recent_messages:
            from_person = msg.get('from', 'unknown')
            content = msg.get('content', '')
            if content:  # Only include non-empty messages
                conversation_summary.append(f"{from_person}: {content}")
        
        if len(global_conversation) > context_limit:
            conversation_summary.append(f"... ({len(global_conversation) - context_limit} earlier messages omitted)")
        
        conversation_summary.append("")  # Empty line separator
        
        # Prepend to prompt
        conversation_text = "\n".join(conversation_summary)
        return f"{conversation_text}\n{prompt}"