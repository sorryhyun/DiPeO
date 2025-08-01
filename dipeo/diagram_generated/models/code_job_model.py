







# Auto-generated Pydantic model for code_job node

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field


from dipeo.diagram_generated.enums import SupportedLanguage


class CodeJobNodeData(BaseModel):
    """Data model for Code Job node."""
    language: SupportedLanguage = Field(description="Programming language")
    filePath: str = Field(description="Path to code file")
    functionName: Optional[str] = Field(description="Function to execute")
    timeout: Optional[int] = Field(description="Execution timeout in seconds")

    class Config:
        extra = "forbid"
        validate_assignment = True