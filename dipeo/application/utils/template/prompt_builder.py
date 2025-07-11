# Unified prompt building service for the application layer.
# This service consolidates prompt-related logic from:
# - dipeo.utils.prompt.builder.PromptBuilder
# - dipeo.application.execution.person_job.prompt_service.PromptProcessingService

from typing import Any, Dict, Optional
import warnings

from dipeo.utils.template import TemplateProcessor
from dipeo.utils.arrow import unwrap_inputs


class PromptBuilder:
    # Unified service for building prompts from templates.
    
    def __init__(self, template_processor: Optional[TemplateProcessor] = None):
        self._processor = template_processor or TemplateProcessor()
    
    def build(
        self,
        prompt: str,
        first_only_prompt: Optional[str] = None,
        execution_count: int = 0,
        template_values: Optional[Dict[str, Any]] = None,
        raw_inputs: Optional[Dict[str, Any]] = None,
    ) -> str:
        # Build a prompt with template substitution.
        selected_prompt = self._select_prompt(prompt, first_only_prompt, execution_count)
        
        if template_values is None:
            if raw_inputs is None:
                template_values = {}
            else:
                template_values = self.prepare_template_values(raw_inputs)
        
        return self._processor.process_simple(selected_prompt, template_values)
    
    def prepare_template_values(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        # Prepare values for template substitution.
        import logging
        logger = logging.getLogger(__name__)
        
        logger.debug(f"prepare_template_values - Raw inputs: {inputs}")
        
        # First unwrap any arrow-processed inputs
        unwrapped_inputs = unwrap_inputs(inputs)
        
        logger.debug(f"prepare_template_values - Unwrapped inputs: {unwrapped_inputs}")
        
        template_values = {}
        
        for key, value in unwrapped_inputs.items():
            # Handle simple types directly
            if isinstance(value, (str, int, float, bool, type(None))):
                template_values[key] = value
            
            # Handle dicts carefully
            elif isinstance(value, dict):
                # Skip conversation states and complex objects
                if "messages" in value:
                    continue
                    
                # Check if this is a NodeOutput-like dict with 'value' key
                if "value" in value and isinstance(value["value"], dict) and "default" in value["value"]:
                    # Extract the default value from NodeOutput-like structure
                    template_values[key] = value["value"]["default"]
                elif all(isinstance(v, (str, int, float, bool, type(None))) for v in value.values()):
                    # Simple dict with all simple values
                    template_values[key] = value
            
            # Handle lists of simple values
            elif isinstance(value, list) and all(isinstance(v, (str, int, float, bool)) for v in value):
                template_values[key] = value
        
        logger.debug(f"prepare_template_values - Final template values: {template_values}")
        
        return template_values
    
    def should_use_first_only_prompt(
        self,
        first_only_prompt: Optional[str],
        execution_count: int
    ) -> bool:
        # Determine if first_only_prompt should be used.
        return bool(first_only_prompt and execution_count == 0)
    
    def _select_prompt(
        self,
        default_prompt: str,
        first_only_prompt: Optional[str],
        execution_count: int,
    ) -> str:
        # Select the appropriate prompt based on execution count.
        if self.should_use_first_only_prompt(first_only_prompt, execution_count):
            return first_only_prompt
        return default_prompt
    
    def build_with_context(
        self,
        prompt: str,
        context: Dict[str, Any],
        first_only_prompt: Optional[str] = None,
        execution_count: int = 0,
    ) -> str:
        # Build a prompt using the full template context capabilities.
        selected_prompt = self._select_prompt(prompt, first_only_prompt, execution_count)
        result = self._processor.process(selected_prompt, context)
        
        # Log any errors or warnings
        if result.errors:
            for error in result.errors:
                warnings.warn(f"Template processing error: {error}", UserWarning)
        
        if result.missing_keys:
            warnings.warn(
                f"Missing template keys: {', '.join(result.missing_keys)}",
                UserWarning
            )
        
        return result.content