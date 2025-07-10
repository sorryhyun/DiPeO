"""Domain service for prompt processing and template substitution."""

from typing import Any, Dict, Optional
import warnings

from dipeo.utils.template import TemplateProcessor


class PromptProcessingService:
    """Service for handling prompt selection and processing for person jobs."""
    
    def __init__(self, template_service: Any = None):
        """Initialize with TemplateProcessor.
        
        Args:
            template_service: Legacy template service (deprecated)
        """
        if template_service is not None:
            warnings.warn(
                "Passing template_service to PromptProcessingService is deprecated. "
                "It now uses the unified TemplateProcessor internally.",
                DeprecationWarning,
                stacklevel=2
            )
        self._processor = TemplateProcessor()
    
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
            
        # Apply template substitution using new processor
        return self._processor.process_simple(template, template_values)
    
    def should_use_first_only_prompt(
        self,
        first_only_prompt: Optional[str],
        execution_count: int
    ) -> bool:
        """Determine if first_only_prompt should be used."""
        return bool(first_only_prompt and execution_count == 0)