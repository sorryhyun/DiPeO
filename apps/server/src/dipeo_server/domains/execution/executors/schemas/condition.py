"""
Condition node schema - boolean logic and branching
"""

from pydantic import Field, field_validator, model_validator
from typing import Optional
from enum import Enum

from .base import BaseNodeProps

# Import ConditionType from original location to avoid duplication
from src.domains.execution.executors.schemas.condition import ConditionType


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
            # Check for basic operators
            operators = ["==", "!=", "<", ">", "<=", ">=", "and", "or", "&&", "||", "true", "false"]
            if not any(op in v for op in operators):
                # This is just a warning, not an error
                # The executor will log a warning but still try to evaluate
                pass
        return v