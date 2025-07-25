# Auto-generated Pydantic model for template_job node

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field




class TemplateJobNodeData(BaseModel):
    """Data model for Template Job node."""
    template_path: Optional[str] = Field(description="Template Path configuration")
    template_content: Optional[str] = Field(description="Template Content configuration")
    output_path: Optional[str] = Field(description="Output Path configuration")
    variables: Optional[Dict[str, Any]] = Field(description="Variables configuration")
    engine: Optional[Literal["internal", "jinja2", "handlebars"]] = Field(description="Engine configuration")

    class Config:
        extra = "forbid"
        validate_assignment = True