"""Domain service for template substitution - backward compatibility wrapper."""

import warnings
from typing import Any, Dict, List, Tuple
from dipeo.utils.template import TemplateProcessor


class TemplateService:
    """Service for handling template substitution with {{placeholders}}.
    
    DEPRECATED: This is a backward compatibility wrapper. 
    Use dipeo.utils.template.TemplateProcessor directly.
    """
    
    def __init__(self):
        self._processor = TemplateProcessor()
        self._deprecation_warned = False
    
    def _warn_deprecation(self):
        if not self._deprecation_warned:
            warnings.warn(
                "dipeo.utils.text.template_service.TemplateService is deprecated. "
                "Use dipeo.utils.template.TemplateProcessor instead.",
                DeprecationWarning,
                stacklevel=3
            )
            self._deprecation_warned = True
    
    def substitute_template(
        self, 
        template: str, 
        values: Dict[str, Any]
    ) -> str:
        """Substitute {{placeholders}} in template with values.
        
        Args:
            template: Template string containing {{placeholders}}
            values: Dictionary of values to substitute
            
        Returns:
            Substituted string
        """
        self._warn_deprecation()
        result = self._processor.process(template, values, track_usage=False)
        return result.content
    
    def substitute_template_with_tracking(
        self, 
        template: str, 
        values: Dict[str, Any]
    ) -> Tuple[str, List[str], List[str]]:
        """Substitute {{placeholders}} in template with values and track usage.
        
        Args:
            template: Template string containing {{placeholders}}
            values: Dictionary of values to substitute
            
        Returns:
            tuple: (substituted_string, list_of_missing_keys, list_of_used_keys)
        """
        self._warn_deprecation()
        result = self._processor.process(template, values, track_usage=True)
        return result.content, result.missing_keys, result.used_keys