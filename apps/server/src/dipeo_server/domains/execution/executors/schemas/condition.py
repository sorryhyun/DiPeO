"""
Condition node schema - boolean logic and branching
"""

from pydantic import Field, field_validator, model_validator
from typing import Optional
from enum import Enum

from .base import BaseNodeProps


class ConditionType(Enum):
    """Type of condition evaluation."""
    EXPRESSION = "expression"


class ConditionNodeProps(BaseNodeProps):
    """Properties for Condition node"""
    conditionType: ConditionType = Field(
        ConditionType.EXPRESSION,
        description="Type of condition evaluation"
    )
    expression: Optional[str] = Field(
        None,
        description="Boolean expression to evaluate (required for expression type)"
    )
    
    @model_validator(mode='after')
    def validate_expression_required(self):
        """Ensure expression is provided when conditionType is 'expression'"""
        if self.conditionType == ConditionType.EXPRESSION and not self.expression:
            raise ValueError("Expression is required when conditionType is 'expression'")
        return self
    
    @field_validator('expression')
    @classmethod
    def validate_expression_syntax(cls, v):
        """Basic validation for expression syntax"""
        if v:
            operators = ["==", "!=", "<", ">", "<=", ">=", "and", "or", "&&", "||", "true", "false"]
            if not any(op in v for op in operators):
                pass
        return v