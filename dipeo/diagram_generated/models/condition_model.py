# Auto-generated Pydantic model for condition node

from typing import *
from pydantic import *


from ..enums import *
from ..integrations import *


class ConditionNodeData(BaseModel):
    """Data model for Condition node."""
    condition_type: Optional[Literal["detect_max_iterations", "check_nodes_executed", "custom"]] = Field(description="Type of condition to evaluate")
    expression: Optional[str] = Field(description="Boolean expression to evaluate")
    node_indices: Optional[List[Any]] = Field(description="Node indices for detect_max_iteration condition")
    expose_index_as: Optional[str] = Field(description="Variable name to expose the condition node's execution count (0-based index) to downstream nodes")

    class Config:
        extra = "forbid"
        validate_assignment = True