







# Auto-generated Pydantic model for template_job node

from typing import *
from pydantic import *


from ..enums import *
from ..integrations import *


class ForeachConfig(BaseModel):
    """Configuration for foreach template rendering."""
    items: Union[List[Any], str] = Field(description="Array or dotted-path string to an array in inputs")
    as_: Optional[str] = Field(default="item", alias="as", description="Variable name to expose each item under in the template")
    output_path: str = Field(description="File path template, e.g. 'dipeo/diagram_generated_staged/models/{{ item.nodeTypeSnake }}.py'")
    limit: Optional[int] = Field(default=None, description="Optional limit on number of items to process")


class PreprocessorConfig(BaseModel):
    """Configuration for template preprocessor."""
    module: str = Field(description="Module path, e.g. 'projects.codegen.code.shared.context_builders'")
    function: str = Field(description="Function name, e.g. 'build_context_from_ast'")
    args: Optional[Dict[str, Any]] = Field(default=None, description="Arguments passed to the preprocessor function")


class TemplateJobNodeData(BaseModel):
    """Data model for Template Job node."""
    template_path: Optional[str] = Field(description="Path to template file")
    template_content: Optional[str] = Field(description="Inline template content")
    output_path: Optional[str] = Field(description="Single-file path; can contain template expressions")
    variables: Optional[Dict[str, Any]] = Field(description="Simple key→value map passed to template; string values are resolved")
    engine: Optional[Literal["internal", "jinja2"]] = Field(description="Template engine to use")
    foreach: Optional[ForeachConfig] = Field(default=None, description="Render a template for each item and write many files")
    preprocessor: Optional[PreprocessorConfig] = Field(default=None, description="Optional Python preprocessor that returns extra context for the template")

    class Config:
        extra = "forbid"
        validate_assignment = True