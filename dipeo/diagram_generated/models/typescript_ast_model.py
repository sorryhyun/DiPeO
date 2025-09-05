# Auto-generated Pydantic model for typescript_ast node

from typing import *
from pydantic import *


from ..enums import *
from ..integrations import *


class TypescriptAstNodeData(BaseModel):
    """Data model for TypeScript AST Parser node."""

    source: str = Field(description="TypeScript source code to parse")

    extract_patterns: Optional[List[Any]] = Field(alias="extractPatterns", description="Patterns to extract from the AST")

    include_js_doc: Optional[bool] = Field(alias="includeJSDoc", description="Include JSDoc comments in the extracted data")

    parse_mode: Optional[Literal["module", "script"]] = Field(alias="parseMode", description="TypeScript parsing mode")

    transform_enums: Optional[bool] = Field(alias="transformEnums", description="Transform enum definitions to a simpler format")

    flatten_output: Optional[bool] = Field(alias="flattenOutput", description="Flatten the output structure for easier consumption")

    output_format: Optional[Literal["standard", "for_codegen", "for_analysis"]] = Field(alias="outputFormat", description="Output format for the parsed data")


    class Config:
        extra = "forbid"
        validate_assignment = True
