# Auto-generated Pydantic model for hook node

from typing import *

from pydantic import *

from ..enums import *
from ..integrations import *


class HookNodeData(BaseModel):
    """Data model for Hook node."""

    hook_type: HookType = Field(description="Type of hook to execute")

    command: Optional[str] = Field(description="Shell command to run (for shell hooks)")

    url: Optional[str] = Field(description="Webhook URL (for HTTP hooks)")

    timeout: Optional[int] = Field(description="Execution timeout in seconds")

    retry_count: Optional[float] = Field(description="Number of retries on failure")

    class Config:
        extra = "forbid"
        validate_assignment = True
