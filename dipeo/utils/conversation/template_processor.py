"""Template processing for conversation messages.

This module provides backward compatibility by delegating to the utils library.
All pure template processing functions have been moved to dipeo.utils.template.
"""

from typing import Dict, Any, List, Optional
from dipeo.utils.template import (
    process_template as _process_template,
    process_conditional_template as _process_conditional_template,
    extract_variables as _extract_variables,
    validate_template as _validate_template,
    create_template_context as _create_template_context,
)


class TemplateProcessor:
    """Processes templates for conversation messages.
    
    This class now delegates to pure functions in dipeo.utils.template
    for better separation of concerns and testability.
    """
    
    @staticmethod
    def process_template(
        template: str,
        context: Dict[str, Any],
        safe: bool = True
    ) -> str:
        """Process a template string with context values.
        
        Delegates to dipeo.utils.template.process_template
        """
        return _process_template(template, context, safe)
    
    @staticmethod
    def process_conditional_template(
        template: str,
        context: Dict[str, Any]
    ) -> str:
        """Process template with conditional sections.
        
        Delegates to dipeo.utils.template.process_conditional_template
        """
        return _process_conditional_template(template, context)
    
    @staticmethod
    def extract_variables(template: str) -> List[str]:
        """Extract all variable names from a template.
        
        Delegates to dipeo.utils.template.extract_variables
        """
        return _extract_variables(template)
    
    @staticmethod
    def validate_template(template: str) -> List[str]:
        """Validate template syntax and return any errors.
        
        Delegates to dipeo.utils.template.validate_template
        """
        return _validate_template(template)
    
    @staticmethod
    def create_template_context(
        variables: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Create a context dictionary for template processing.
        
        Delegates to dipeo.utils.template.create_template_context
        """
        return _create_template_context(variables, metadata)