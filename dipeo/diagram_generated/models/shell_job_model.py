# Auto-generated Pydantic model for shell_job node

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field




class ShellJobNodeData(BaseModel):
    """Data model for Shell Job node."""
    command: str = Field(description="Command configuration")
    args: Optional[List[Any]] = Field(description="Args configuration")
    cwd: Optional[str] = Field(description="Cwd configuration")
    env: Optional[Dict[str, Any]] = Field(description="Env configuration")
    timeout: Optional[float] = Field(description="Timeout configuration")
    capture_output: Optional[bool] = Field(description="Capture Output configuration")
    shell: Optional[bool] = Field(description="Shell configuration")

    class Config:
        extra = "forbid"
        validate_assignment = True