# Auto-generated Pydantic model for condition node

from typing import *

from pydantic import *

from ..enums import *
from ..integrations import *


class ConditionNodeData(BaseModel):
    """Data model for Condition node."""

    condition_type: Optional[Literal["detect_max_iterations", "check_nodes_executed", "custom", "llm_decision"]] = Field(description="Type of condition to evaluate")

    expression: Optional[str] = Field(description="Boolean expression to evaluate")

    node_indices: Optional[List[Any]] = Field(description="Node indices for detect_max_iteration condition")

    person: Optional[str] = Field(description="AI agent to use for decision making")

    judge_by: Optional[str] = Field(description="Prompt for LLM to make a judgment")

    judge_by_file: Optional[str] = Field(description="External prompt file path")

    memorize_to: Optional[str] = Field(description="Memory control strategy (e.g., GOLDFISH for fresh evaluation)")

    at_most: Optional[float] = Field(description="Maximum messages to keep in memory")

    expose_index_as: Optional[str] = Field(description="Variable name to expose the condition node's execution count (0-based index) to downstream nodes")

    skippable: Optional[bool] = Field(description="When true, downstream nodes can execute even if this condition hasn't been evaluated yet")


    class Config:
        extra = "forbid"
        validate_assignment = True
