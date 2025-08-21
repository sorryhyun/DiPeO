"""Runtime transformation engine for applying data transformations.

This module provides the engine for applying transformation rules to values
during runtime execution.
"""

from typing import Any
from abc import ABC, abstractmethod

from dipeo.domain.diagram.compilation import TransformRules


class TransformationEngine(ABC):
    """Base class for applying data transformations based on content types.
    
    This engine applies transformation rules determined at compile-time
    to values during runtime execution.
    """
    
    @abstractmethod
    def transform(
        self,
        value: Any,
        rules: TransformRules,
        source_content_type: str | None = None,
        target_content_type: str | None = None
    ) -> Any:
        """Apply transformation rules to a value.
        
        Args:
            value: The value to transform
            rules: Transformation rules to apply
            source_content_type: Optional source content type
            target_content_type: Optional target content type
            
        Returns:
            The transformed value
        """
        pass


class StandardTransformationEngine(TransformationEngine):
    """Standard implementation of the transformation engine."""
    
    def transform(
        self,
        value: Any,
        rules: TransformRules | list[dict] | str | None,
        source_content_type: str | None = None,
        target_content_type: str | None = None
    ) -> Any:
        """Apply transformation rules to a value.
        
        This implementation supports multiple rule formats for backward compatibility:
        - TransformRules object (preferred)
        - List of dict rules (legacy)
        - String rules (legacy)
        
        Args:
            value: The value to transform
            rules: Transformation rules in various formats
            source_content_type: Optional source content type (unused currently)
            target_content_type: Optional target content type (unused currently)
            
        Returns:
            Transformed value
        """
        if not rules:
            return value
        
        # Handle TransformRules object
        if isinstance(rules, TransformRules):
            rules_to_apply = rules.rules.get('transforms', [])
            if not rules_to_apply:
                # Check for direct rules
                rules_to_apply = list(rules.rules.values())
        # Handle string rules (legacy format)
        elif isinstance(rules, str):
            if rules == "default":
                return value
            return value
        # Handle list of rules
        elif isinstance(rules, list):
            rules_to_apply = rules
        else:
            return value
        
        # Apply each rule in sequence
        result = value
        for rule in rules_to_apply:
            if not rule:
                continue
            if isinstance(rule, str):
                continue
            result = self._apply_rule(result, rule)
        
        return result
    
    def _apply_rule(self, value: Any, rule: dict) -> Any:
        """Apply a single transformation rule.
        
        Args:
            value: The value to transform
            rule: The transformation rule as a dict
            
        Returns:
            Transformed value
        """
        rule_type = rule.get('type')
        
        if rule_type == 'extract':
            # Extract a field from a dict
            if isinstance(value, dict):
                field = rule.get('field')
                if field:
                    return value.get(field)
        
        elif rule_type == 'wrap':
            # Wrap value in a dict
            key = rule.get('key', 'value')
            return {key: value}
        
        elif rule_type == 'map':
            # Map values
            mapping = rule.get('mapping', {})
            if value in mapping:
                return mapping[value]
        
        elif rule_type == 'template':
            # Apply template transformation
            template = rule.get('template', '')
            if isinstance(value, dict):
                return template.format(**value)
            else:
                return template.format(value=value)
        
        elif rule_type == 'json':
            # Parse JSON string
            import json
            if isinstance(value, str):
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value
        
        # Default: return value unchanged
        return value