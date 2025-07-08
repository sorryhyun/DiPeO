"""Domain service for building prompts from templates."""

from typing import Any, Dict, Optional


class PromptBuilder:
    """Builds prompts from templates with template substitution.
    
    Single Responsibility: Template selection and substitution for prompts.
    """
    
    def build_prompt(
        self,
        default_prompt: str,
        first_only_prompt: Optional[str],
        execution_count: int,
        template_values: Dict[str, Any],
        template_substitutor: Any,  # Protocol for template substitution
    ) -> str:
        """Build the appropriate prompt for the current execution.
        
        Args:
            default_prompt: The default prompt template
            first_only_prompt: Optional prompt to use on first execution only
            execution_count: Current execution count (0-based)
            template_values: Values to substitute in the template
            template_substitutor: Service that performs template substitution
            
        Returns:
            The built prompt with substitutions applied
        """
        # Select appropriate prompt based on execution count
        selected_prompt = self._select_prompt(
            default_prompt=default_prompt,
            first_only_prompt=first_only_prompt,
            execution_count=execution_count,
        )
        
        # Apply template substitution
        return template_substitutor.substitute_template(
            selected_prompt,
            template_values
        )
    
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
        template_values = {}
        
        for key, value in inputs.items():
            # Skip conversation states and complex objects
            if isinstance(value, (str, int, float, bool)):
                template_values[key] = value
            elif isinstance(value, dict) and "messages" not in value:
                # Simple dict might be okay if all values are simple types
                if all(isinstance(v, (str, int, float, bool)) for v in value.values()):
                    template_values[key] = value
        
        return template_values