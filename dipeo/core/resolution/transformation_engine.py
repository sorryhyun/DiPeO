"""Transformation engine interface for applying data transformations.

This interface defines how transformation rules are applied to values
as they flow between nodes.
"""

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Protocol

from dipeo.diagram_generated import ContentType
from .interfaces import TransformationEngine as TransformationEngineBase, TransformRules


class TransformationRule(Protocol):
    """Protocol for individual transformation rules."""
    
    @property
    def rule_type(self) -> str:
        """Type identifier for this rule."""
        ...
    
    def can_apply(self, value: Any, config: Any) -> bool:
        """Check if this rule can be applied to the value."""
        ...
    
    def apply(self, value: Any, config: Any) -> Any:
        """Apply the transformation to the value."""
        ...


class TransformationEngine(TransformationEngineBase, ABC):
    """Abstract base class for transformation engines.
    
    This extends the core TransformationEngine with additional
    methods for managing transformation rules.
    """
    
    @abstractmethod
    def register_transformer(self, rule_type: str, transformer: TransformationRule) -> None:
        """Register a transformer for a specific rule type."""
        pass
    
    @abstractmethod
    def transform(self, value: Any, rules: dict[str, Any]) -> Any:
        """Apply all transformation rules to a value.
        
        Args:
            value: The value to transform
            rules: Dictionary of rule_type -> rule_config
            
        Returns:
            Transformed value
        """
        pass
    
    @abstractmethod
    def has_transformer(self, rule_type: str) -> bool:
        """Check if a transformer is registered for a rule type."""
        pass


class VariableExtractor:
    """Extracts variables from complex objects."""
    
    @property
    def rule_type(self) -> str:
        return "extract_variable"
    
    def can_apply(self, value: Any, config: Any) -> bool:
        """Can apply if value is dict-like and has the variable."""
        if not isinstance(config, str):
            return False
        return hasattr(value, '__getitem__') and config in value
    
    def apply(self, value: Any, config: Any) -> Any:
        """Extract variable from value."""
        if isinstance(config, str) and hasattr(value, '__getitem__'):
            return value.get(config) if hasattr(value, 'get') else value[config]
        return value


class Formatter:
    """Applies format strings to values."""
    
    @property
    def rule_type(self) -> str:
        return "format"
    
    def can_apply(self, value: Any, config: Any) -> bool:
        """Can apply if config is a format string."""
        return isinstance(config, str) and '{' in config
    
    def apply(self, value: Any, config: Any) -> Any:
        """Apply format string."""
        if isinstance(config, str):
            try:
                return config.format(value=value)
            except Exception:
                return str(value)
        return value


class ContentTypeConverter:
    """Converts values to match expected content types."""
    
    @property
    def rule_type(self) -> str:
        return "content_type_conversion"
    
    def can_apply(self, value: Any, config: Any) -> bool:
        """Can apply if content type is specified."""
        return isinstance(config, str | ContentType)
    
    def apply(self, value: Any, config: Any) -> Any:
        """Convert value to match content type."""
        content_type = config.value if hasattr(config, 'value') else config
        
        if content_type == 'object' and isinstance(value, str):
            # Try to parse JSON strings for object content type
            if value.strip() and value.strip()[0] in '{[':
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    logging.debug("Could not parse JSON for object content type")
        
        elif content_type == 'string' and not isinstance(value, str):
            return str(value)
        
        elif content_type == 'number':
            try:
                return float(value) if '.' in str(value) else int(value)
            except (ValueError, TypeError):
                pass
        
        elif content_type == 'boolean':
            if isinstance(value, str):
                return value.lower() in ('true', '1', 'yes')
            return bool(value)
        
        return value


class ExtractToolResults:
    """Extracts tool results from PersonJob outputs."""
    
    @property
    def rule_type(self) -> str:
        return "extract_tool_results"
    
    def can_apply(self, value: Any, config: Any) -> bool:
        """Can apply if config is True and value has tool_results."""
        return config is True and hasattr(value, 'get') and 'tool_results' in value
    
    def apply(self, value: Any, config: Any) -> Any:
        """Extract tool results."""
        if hasattr(value, 'get') and 'tool_results' in value:
            return value['tool_results']
        return value


class BranchOnCondition:
    """Handles branching based on condition results."""
    
    @property  
    def rule_type(self) -> str:
        return "branch_on"
    
    def can_apply(self, value: Any, config: Any) -> bool:
        """Can apply for condition branching."""
        return config == "condition_result"
    
    def apply(self, value: Any, config: Any) -> Any:
        """Apply condition branching logic."""
        # This is handled specially in edge processing
        return value


class StandardTransformationEngine(TransformationEngine):
    """Standard implementation of the transformation engine."""
    
    def __init__(self):
        self.transformers: dict[str, TransformationRule] = {}
        self._register_default_transformers()
    
    def _register_default_transformers(self) -> None:
        """Register built-in transformers."""
        self.register_transformer("extract_variable", VariableExtractor())
        self.register_transformer("format", Formatter())
        self.register_transformer("content_type_conversion", ContentTypeConverter())
        self.register_transformer("extract_tool_results", ExtractToolResults())
        self.register_transformer("branch_on", BranchOnCondition())
    
    def register_transformer(self, rule_type: str, transformer: TransformationRule) -> None:
        """Register a transformer for a specific rule type."""
        self.transformers[rule_type] = transformer
    
    def transform(self, value: Any, rules: dict[str, Any]) -> Any:
        """Apply all transformation rules to a value."""
        result = value
        
        # Apply transformations in a specific order for consistency
        ordered_rules = [
            ("extract_variable", rules.get("extract_variable")),
            ("extract_tool_results", rules.get("extract_tool_results")),
            ("format", rules.get("format")),
            ("content_type_conversion", rules.get("content_type")),
            ("branch_on", rules.get("branch_on")),
        ]
        
        for rule_type, rule_config in ordered_rules:
            if rule_config is not None and rule_type in self.transformers:
                transformer = self.transformers[rule_type]
                if transformer.can_apply(result, rule_config):
                    result = transformer.apply(result, rule_config)
        
        # Apply any custom rules not in the ordered list
        for rule_type, rule_config in rules.items():
            if rule_type not in [r[0] for r in ordered_rules] and rule_type in self.transformers:
                    transformer = self.transformers[rule_type]
                    if transformer.can_apply(result, rule_config):
                        result = transformer.apply(result, rule_config)
        
        return result
    
    def has_transformer(self, rule_type: str) -> bool:
        """Check if a transformer is registered for a rule type."""
        return rule_type in self.transformers