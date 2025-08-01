# Auto-generated Pydantic model for template_job node

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field




class TemplateJobNodeData(BaseModel):
    """Data model for Template Job node."""
    template_path: Optional[str] = Field(description="Path to template file")
    template_content: Optional[str] = Field(description="Inline template content")
    output_path: Optional[str] = Field(description="Output file path")
    variables: Optional[Dict[str, Any]] = Field(description="Variables configuration")
    engine: Optional[str] = Field(description="Engine configuration")

    class Config:
        extra = "forbid"
        validate_assignment = True