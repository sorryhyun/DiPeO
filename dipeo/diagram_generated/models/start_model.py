# Auto-generated Pydantic model for start node

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field




class StartNodeData(BaseModel):
    """Data model for Start Node node."""
    custom_data: str = Field(description="Custom Data configuration")
    output_data_structure: Dict[str, Any] = Field(description="Output Data Structure configuration")
    trigger_mode: Optional[Literal["manual", "hook"]] = Field(description="Trigger Mode configuration")
    hook_event: Optional[str] = Field(description="Hook Event configuration")
    hook_filters: Optional[Dict[str, Any]] = Field(description="Hook Filters configuration")

    class Config:
        extra = "forbid"
        validate_assignment = True