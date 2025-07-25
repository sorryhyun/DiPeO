# Auto-generated Pydantic model for endpoint node

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field




class EndpointNodeData(BaseModel):
    """Data model for End Node node."""
    save_to_file: bool = Field(description="Save To File configuration")
    file_name: Optional[str] = Field(description="File Name configuration")

    class Config:
        extra = "forbid"
        validate_assignment = True