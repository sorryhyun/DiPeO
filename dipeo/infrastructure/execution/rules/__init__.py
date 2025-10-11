"""Infrastructure for execution rule registry and management."""

from .adapters import (
    EndpointNoOutputRule,
    OutputCapableRule,
    PersonJobToolExtractionRule,
    StartNoInputRule,
    register_default_rules,
)
from .base import (
    BaseConnectionRule,
    BaseTransformRule,
    ConnectionRule,
    RuleCategory,
    RulePriority,
    TransformRule,
)
from .registry import ExecutionRuleRegistry, RuleKey

__all__ = [
    "BaseConnectionRule",
    "BaseTransformRule",
    "ConnectionRule",
    "EndpointNoOutputRule",
    "ExecutionRuleRegistry",
    "OutputCapableRule",
    "PersonJobToolExtractionRule",
    "RuleCategory",
    "RuleKey",
    "RulePriority",
    "StartNoInputRule",
    "TransformRule",
    "register_default_rules",
]
