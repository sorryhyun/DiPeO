"""Domain service for building prompts from templates."""

from typing import Any, Dict, Optional
import warnings
from dipeo.utils.template import TemplateProcessor


class PromptBuilder:
    """Builds prompts from templates with template substitution.
    
    Single Responsibility: Template selection and substitution for prompts.
    """
    
    def __init__(self):
        """Initialize with new TemplateProcessor."""
        self._processor = TemplateProcessor()
    
    def build_prompt(
        self,
        default_prompt: str,
        first_only_prompt: Optional[str],
        execution_count: int,
        template_values: Dict[str, Any],
        template_substitutor: Any = None,  # Protocol for template substitution (deprecated)
    ) -> str:
        """Build the appropriate prompt for the current execution.
        
        Args:
            default_prompt: The default prompt template
            first_only_prompt: Optional prompt to use on first execution only
            execution_count: Current execution count (0-based)
            template_values: Values to substitute in the template
            template_substitutor: Service that performs template substitution (deprecated, use internal processor)
            
        Returns:
            The built prompt with substitutions applied
        """
        # Deprecation warning if old template_substitutor is passed
        if template_substitutor is not None:
            warnings.warn(
                "Passing template_substitutor to build_prompt is deprecated. "
                "PromptBuilder now uses the unified TemplateProcessor internally.",
                DeprecationWarning,
                stacklevel=2
            )
        
        # Select appropriate prompt based on execution count
        selected_prompt = self._select_prompt(
            default_prompt=default_prompt,
            first_only_prompt=first_only_prompt,
            execution_count=execution_count,
        )
        
        # Apply template substitution using new processor
        return self._processor.process_simple(selected_prompt, template_values)
    
    def _select_prompt(
        self,
        default_prompt: str,
        first_only_prompt: Optional[str],
        execution_count: int,
    ) -> str:
        """Select the appropriate prompt based on execution count."""
        if first_only_prompt and execution_count == 0:
            return first_only_prompt
        return default_prompt
    
    def prepare_template_values(
        self,
        inputs: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Prepare values for template substitution.
        
        Filters out complex objects that shouldn't be in templates.
        """
        # First unwrap any arrow-processed inputs
        from dipeo.utils.arrow import unwrap_inputs
        unwrapped_inputs = unwrap_inputs(inputs)
        
        template_values = {}
        
        for key, value in unwrapped_inputs.items():
            # Skip conversation states and complex objects
            if isinstance(value, (str, int, float, bool)):
                template_values[key] = value
            elif isinstance(value, dict) and "messages" not in value:
                # Check if this is a NodeOutput-like dict with 'value' key
                if "value" in value and isinstance(value["value"], dict) and "default" in value["value"]:
                    # Extract the default value from NodeOutput-like structure
                    template_values[key] = value["value"]["default"]
                elif all(isinstance(v, (str, int, float, bool)) for v in value.values()):
                    # Simple dict with all simple values
                    template_values[key] = value
        
        return template_values