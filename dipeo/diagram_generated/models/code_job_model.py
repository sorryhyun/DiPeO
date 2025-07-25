# Auto-generated Pydantic model for code_job node

from typing import Optional, Dict, Any, List, Literal
from pydantic import BaseModel, Field


from dipeo.models.models import SupportedLanguage


class CodeJobNodeData(BaseModel):
    """Data model for Code Job node."""
    language: SupportedLanguage = Field(description="Language configuration")
    filePath: str = Field(description="Filepath configuration")
    functionName: Optional[str] = Field(description="Functionname configuration")
    timeout: Optional[float] = Field(description="Timeout configuration")

    class Config:
        extra = "forbid"
        validate_assignment = True