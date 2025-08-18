"""Simplified transformation engine for applying data transformations."""

from typing import Any


class StandardTransformationEngine:
    """Engine for applying transformation rules to values."""
    
    def transform(self, value: Any, rules: list[dict] | str | None) -> Any:
        """Apply transformation rules to a value.
        
        Args:
            value: The value to transform
            rules: List of transformation rules, a string rule, or None
            
        Returns:
            Transformed value
        """
        if not rules:
            return value
            
        # Handle string rules (legacy format)
        if isinstance(rules, str):
            # Simple string transformations like "default"
            if rules == "default":
                # Return value as-is for default
                return value
            # Otherwise treat as pass-through
            return value
        
        # Handle list of rules (could be dicts or strings)
        result = value
        
        for rule in rules:
            # Skip if rule is None or empty
            if not rule:
                continue
            # Handle string rules in list
            if isinstance(rule, str):
                # Simple pass-through for string rules in lists
                continue
            # Handle dict rules
            result = self._apply_rule(result, rule)
        
        return result
    
    def _apply_rule(self, value: Any, rule: dict) -> Any:
        """Apply a single transformation rule."""
        
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