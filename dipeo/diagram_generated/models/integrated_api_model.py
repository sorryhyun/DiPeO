







# Auto-generated Pydantic model for integrated_api node

from typing import *
from pydantic import *


from ..enums import *
from ..integrations import *


class IntegratedApiNodeData(BaseModel):
    """Data model for Integrated API node."""
    provider: Literal["notion", "slack", "github", "jira", "google_search"] = Field(description="API provider to connect to")
    operation: NotionOperation = Field(description="Operation to perform (provider-specific)")
    resource_id: Optional[str] = Field(description="Resource identifier (e.g., page ID, channel ID)")
    config: Optional[Dict[str, Any]] = Field(description="Provider-specific configuration")
    timeout: Optional[int] = Field(description="Request timeout in seconds")
    max_retries: Optional[float] = Field(description="Maximum retry attempts")

    class Config:
        extra = "forbid"
        validate_assignment = True