







# Auto-generated Pydantic model for typescript_ast node

from typing import *
from pydantic import *


from ..enums import *
from ..integrations import *


class TypescriptAstNodeData(BaseModel):
    """Data model for TypeScript AST Parser node."""
    source: Optional[str] = Field(default=None, description="TypeScript source code to parse")
    extractPatterns: Optional[List[Any]] = Field(default=None, description="Patterns to extract from the AST")
    includeJSDoc: Optional[bool] = Field(default=None, description="Include JSDoc comments in the extracted data")
    parseMode: Optional[Literal["module", "script"]] = Field(default=None, description="TypeScript parsing mode")
    transformEnums: Optional[bool] = Field(default=None, description="Transform enum definitions to a simpler format")
    flattenOutput: Optional[bool] = Field(default=None, description="Flatten the output structure for easier consumption")
    outputFormat: Optional[Literal["standard", "for_codegen", "for_analysis"]] = Field(default=None, description="Output format for the parsed data")
    batch: Optional[bool] = Field(default=None, description="Enable batch mode for parsing multiple sources")
    sources: Optional[Dict[str, str]] = Field(default=None, description="Dictionary of sources to parse in batch mode")
    batchInputKey: Optional[str] = Field(default=None, description="Input key to look for sources dictionary")

    class Config:
        extra = "forbid"
        validate_assignment = True