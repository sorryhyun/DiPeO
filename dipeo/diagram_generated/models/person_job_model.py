







# Auto-generated Pydantic model for person_job node

from typing import *
from pydantic import *


from ..domain_models import *

from ..enums import *
from ..integrations import *


class PersonJobNodeData(BaseModel):
    """Data model for Person Job node."""
    person: Optional[str] = Field(description="AI person to use")
    first_only_prompt: str = Field(description="Prompt used only on first execution")
    default_prompt: Optional[str] = Field(description="Default prompt template")
    prompt_file: Optional[str] = Field(description="Path to prompt file in /files/prompts/")
    max_iteration: int = Field(description="Maximum execution iterations")
    memory_profile: Optional[str] = Field(description="Memory profile for conversation context")
    tools: Optional[List[ToolConfig]] = Field(description="Tools available to the AI agent")
    memory_settings: Optional[MemorySettings] = Field(description="Custom memory settings (when memory_profile is CUSTOM)")

    class Config:
        extra = "forbid"
        validate_assignment = True