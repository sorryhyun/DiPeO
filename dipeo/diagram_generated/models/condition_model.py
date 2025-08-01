







# Auto-generated Pydantic model for condition node

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field




class ConditionNodeData(BaseModel):
    """Data model for Condition node."""
    condition_type: str = Field(description="Type of condition to evaluate")
    expression: Optional[str] = Field(description="Boolean expression to evaluate")
    node_indices: Optional[List[Any]] = Field(description="Node indices for condition evaluation")

    class Config:
        extra = "forbid"
        validate_assignment = True