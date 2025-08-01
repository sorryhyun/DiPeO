







# Auto-generated Pydantic model for api_job node

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field


from dipeo.diagram_generated.enums import HttpMethod


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