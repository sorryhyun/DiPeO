"""Unified prompt building service for the application layer.

This service consolidates prompt-related logic from:
- dipeo.utils.prompt.builder.PromptBuilder
- dipeo.application.execution.person_job.prompt_service.PromptProcessingService
"""

from typing import Any, Dict, Optional
import warnings

from dipeo.utils.template import TemplateProcessor
from dipeo.utils.arrow import unwrap_inputs


class PromptBuilder:
    """Unified service for building prompts from templates.
    
    This service handles:
    - Prompt selection (first_only vs default)
    - Template value preparation and arrow unwrapping
    - Template substitution using the unified processor
    - Execution count handling
    """
    
    def __init__(self, template_processor: Optional[TemplateProcessor] = None):
        """Initialize with optional template processor.
        
        Args:
            template_processor: Optional template processor instance.
                              If not provided, creates a new one.
        """
        self._processor = template_processor or TemplateProcessor()
    
    def build(
        self,
        prompt: str,
        first_only_prompt: Optional[str] = None,
        execution_count: int = 0,
        template_values: Optional[Dict[str, Any]] = None,
        raw_inputs: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Build a prompt with template substitution.
        
        Args:
            prompt: The default prompt template
            first_only_prompt: Optional prompt to use on first execution only
            execution_count: Current execution count (0-based)
            template_values: Pre-processed values for template substitution
            raw_inputs: Raw inputs to process (will be prepared if template_values not provided)
            
        Returns:
            The built prompt with substitutions applied
        """
        # Select appropriate prompt
        selected_prompt = self._select_prompt(prompt, first_only_prompt, execution_count)
        
        # Prepare template values if not provided
        if template_values is None:
            if raw_inputs is None:
                template_values = {}
            else:
                template_values = self.prepare_template_values(raw_inputs)
        
        # Apply template substitution
        return self._processor.process_simple(selected_prompt, template_values)
    
    # Backward compatibility methods
    def build_prompt(
        self,
        default_prompt: str,
        first_only_prompt: Optional[str],
        execution_count: int,
        template_values: Dict[str, Any],
        template_substitutor: Any = None,
    ) -> str:
        """Legacy method for backward compatibility with utils.prompt.builder.
        
        @deprecated Use build() instead.
        """
        if template_substitutor is not None:
            warnings.warn(
                "template_substitutor parameter is deprecated and ignored. "
                "PromptBuilder uses the unified TemplateProcessor internally.",
                DeprecationWarning,
                stacklevel=2
            )
        
        return self.build(
            prompt=default_prompt,
            first_only_prompt=first_only_prompt,
            execution_count=execution_count,
            template_values=template_values
        )
    
    def get_prompt_for_execution(
        self,
        prompt: str,
        first_only_prompt: Optional[str],
        execution_count: int,
        template_values: Dict[str, Any]
    ) -> str:
        """Legacy method for backward compatibility with prompt_service.
        
        @deprecated Use build() instead.
        """
        return self.build(
            prompt=prompt,
            first_only_prompt=first_only_prompt,
            execution_count=execution_count,
            template_values=template_values
        )
    
    # Core functionality
    def prepare_template_values(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare values for template substitution.
        
        This method:
        - Unwraps arrow-processed inputs
        - Filters out complex objects that shouldn't be in templates
        - Extracts simple values suitable for template substitution
        
        Args:
            inputs: Raw input dictionary
            
        Returns:
            Dictionary of template-safe values
        """
        # First unwrap any arrow-processed inputs
        unwrapped_inputs = unwrap_inputs(inputs)
        
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
        
        return template_values
    
    def should_use_first_only_prompt(
        self,
        first_only_prompt: Optional[str],
        execution_count: int
    ) -> bool:
        """Determine if first_only_prompt should be used.
        
        Args:
            first_only_prompt: The first-only prompt template
            execution_count: Current execution count
            
        Returns:
            True if first_only_prompt should be used
        """
        return bool(first_only_prompt and execution_count == 0)
    
    def _select_prompt(
        self,
        default_prompt: str,
        first_only_prompt: Optional[str],
        execution_count: int,
    ) -> str:
        """Select the appropriate prompt based on execution count.
        
        Business rule: Use first_only_prompt on first execution (count=0) if provided,
        otherwise use default_prompt.
        """
        if self.should_use_first_only_prompt(first_only_prompt, execution_count):
            return first_only_prompt
        return default_prompt
    
    # Advanced features
    def build_with_context(
        self,
        prompt: str,
        context: Dict[str, Any],
        first_only_prompt: Optional[str] = None,
        execution_count: int = 0,
    ) -> str:
        """Build a prompt using the full template context capabilities.
        
        This method uses the full TemplateProcessor features including:
        - Conditionals: {{#if condition}}...{{/if}}
        - Loops: {{#each items}}...{{/each}}
        - Nested access: {{user.name}}
        
        Args:
            prompt: The prompt template
            context: Full context dictionary for template processing
            first_only_prompt: Optional first-execution-only prompt
            execution_count: Current execution count
            
        Returns:
            The processed prompt
        """
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