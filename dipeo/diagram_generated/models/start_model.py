# Auto-generated Pydantic model for start node

from typing import *
from pydantic import *


from ..enums import *
from ..integrations import *


class StartNodeData(BaseModel):
    """Data model for Start Node node."""

    trigger_mode: HookTriggerMode = Field(description="How this start node is triggered")

    custom_data: Optional[str] = Field(description="Custom data to pass when manually triggered")

    output_data_structure: Optional[Dict[str, Any]] = Field(description="Expected output data structure")

    hook_event: Optional[str] = Field(description="Event name to listen for")

    hook_filters: Optional[Dict[str, Any]] = Field(description="Filters to apply to incoming events")


    class Config:
        extra = "forbid"
        validate_assignment = True