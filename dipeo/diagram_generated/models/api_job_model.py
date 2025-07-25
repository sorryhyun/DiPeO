# Auto-generated Pydantic model for api_job node

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field




class ApiJobNodeData(BaseModel):
    """Data model for API Job node."""
    url: str = Field(description="Url configuration")
    method: Literal["GET", "POST", "PUT", "DELETE", "PATCH"] = Field(description="Method configuration")
    headers: Optional[Dict[str, Any]] = Field(description="Headers configuration")
    params: Optional[Dict[str, Any]] = Field(description="Params configuration")
    body: Optional[Dict[str, Any]] = Field(description="Body configuration")
    timeout: Optional[float] = Field(description="Timeout configuration")
    auth_type: Optional[Literal["none", "bearer", "basic", "api_key"]] = Field(description="Auth Type configuration")
    auth_config: Optional[Dict[str, Any]] = Field(description="Auth Config configuration")

    class Config:
        extra = "forbid"
        validate_assignment = True