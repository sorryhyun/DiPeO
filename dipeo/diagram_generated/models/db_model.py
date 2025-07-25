# Auto-generated Pydantic model for db node

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field




class DbNodeData(BaseModel):
    """Data model for Database node."""
    file: Optional[str] = Field(description="File configuration")
    collection: Optional[str] = Field(description="Collection configuration")
    sub_type: Literal["fixed_prompt", "file", "code", "api_tool"] = Field(description="Sub Type configuration")
    operation: str = Field(description="Operation configuration")
    query: Optional[str] = Field(description="Query configuration")
    data: Optional[Dict[str, Any]] = Field(description="Data configuration")

    class Config:
        extra = "forbid"
        validate_assignment = True