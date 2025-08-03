







# Auto-generated Pydantic model for api_job node

from typing import *
from pydantic import *


from ..enums import *
from ..integrations import *


class ApiJobNodeData(BaseModel):
    """Data model for API Job node."""
    url: str = Field(description="API endpoint URL")
    method: HttpMethod = Field(description="HTTP method")
    headers: Optional[Dict[str, Any]] = Field(description="HTTP headers")
    params: Optional[Dict[str, Any]] = Field(description="Query parameters")
    body: Optional[Dict[str, Any]] = Field(description="Request body")
    timeout: Optional[int] = Field(description="Request timeout in seconds")
    auth_type: Optional[Literal["none", "bearer", "basic", "api_key"]] = Field(description="Authentication type")
    auth_config: Optional[Dict[str, Any]] = Field(description="Authentication configuration")

    class Config:
        extra = "forbid"
        validate_assignment = True