







# Auto-generated Pydantic model for template_job node

from typing import *
from pydantic import *


from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class TemplateJobNodeData(BaseModel):
    """Data model for Template Job node."""
    template_path: Optional[str] = Field(description="Path to template file")
    template_content: Optional[str] = Field(description="Inline template content")
    output_path: Optional[str] = Field(description="Output file path")
    variables: Optional[Dict[str, Any]] = Field(description="Variables configuration")
    engine: Optional[Literal["internal", "jinja2", "handlebars"]] = Field(description="Template engine to use")

    class Config:
        extra = "forbid"
        validate_assignment = True