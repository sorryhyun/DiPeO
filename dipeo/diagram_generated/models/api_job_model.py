# Auto-generated Pydantic model for api_job node

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field


from dipeo.diagram_generated.enums import HttpMethod


class ApiJobNodeData(BaseModel):
    """Data model for API Job node."""
    url: str = Field(description="Url configuration")
    method: HttpMethod = Field(description="Method configuration")
    headers: Optional[Dict[str, Any]] = Field(description="Headers configuration")
    params: Optional[Dict[str, Any]] = Field(description="Params configuration")
    body: Optional[Dict[str, Any]] = Field(description="Body configuration")
    timeout: Optional[float] = Field(description="Timeout configuration")
    auth_type: Optional[str] = Field(description="Auth Type configuration")
    auth_config: Optional[Dict[str, Any]] = Field(description="Auth Config configuration")

    class Config:
        extra = "forbid"
        validate_assignment = True