







# Auto-generated Pydantic model for code_job node

from typing import *
from pydantic import *


from ..enums import *
from ..integrations import *


class CodeJobNodeData(BaseModel):
    """Data model for Code Job node."""
    language: SupportedLanguage = Field(description="Programming language")
    filePath: Optional[str] = Field(description="Path to code file")
    code: Optional[str] = Field(description="Inline code to execute (alternative to filePath)")
    functionName: Optional[str] = Field(description="Function to execute")
    timeout: Optional[int] = Field(description="Execution timeout in seconds")

    class Config:
        extra = "forbid"
        validate_assignment = True