# Auto-generated Pydantic model for condition node

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field




class ConditionNodeData(BaseModel):
    """Data model for Condition node."""
    condition_type: str = Field(description="Condition Type configuration")
    expression: Optional[str] = Field(description="Expression configuration")
    node_indices: Optional[List[Any]] = Field(description="Node Indices configuration")

    class Config:
        extra = "forbid"
        validate_assignment = True