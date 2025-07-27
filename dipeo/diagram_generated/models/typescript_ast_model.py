# Auto-generated Pydantic model for typescript_ast node

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field




class TypescriptAstNodeData(BaseModel):
    """Data model for TypeScript AST Parser node."""
    source: str = Field(description="TypeScript source code to parse")
    extractPatterns: Optional[List[Any]] = Field(description="Patterns to extract from the AST")
    includeJSDoc: Optional[bool] = Field(description="Include JSDoc comments in the extracted data")
    parseMode: Optional[str] = Field(description="TypeScript parsing mode")
    transformEnums: Optional[bool] = Field(description="Transform enum definitions to a simpler format")
    flattenOutput: Optional[bool] = Field(description="Flatten the output structure for easier consumption")
    outputFormat: Optional[str] = Field(description="Output format for the parsed data")

    class Config:
        extra = "forbid"
        validate_assignment = True