"""Domain service for prompt processing and template substitution."""

from typing import Any, Dict, Optional

from dipeo.utils.text.template_service import TemplateService


class PromptProcessingService:
    """Service for handling prompt selection and processing for person jobs."""
    
    def __init__(self, template_service: TemplateService):
        self._template_service = template_service
    
    def get_prompt_for_execution(
        self,
        prompt: str,
        first_only_prompt: Optional[str],
        execution_count: int,
        template_values: Dict[str, Any]
    ) -> str:
        """
        Get the appropriate prompt for the current execution.
        
        Business rules:
        - Use first_only_prompt if set and this is the first execution
        - Otherwise use default_prompt
        - Apply template substitution to the selected prompt
        """
        # Select appropriate prompt based on execution count
        if first_only_prompt and execution_count == 0:
            template = first_only_prompt
        else:
            template = prompt
            
        # Apply template substitution
        return self._template_service.substitute_template(template, template_values)
    
    def should_use_first_only_prompt(
        self,
        first_only_prompt: Optional[str],
        execution_count: int
    ) -> bool:
        """Determine if first_only_prompt should be used."""
        return bool(first_only_prompt and execution_count == 0)