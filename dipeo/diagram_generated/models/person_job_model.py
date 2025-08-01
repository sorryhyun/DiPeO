







# Auto-generated Pydantic model for person_job node

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


from dipeo.diagram_generated.domain_models import PersonID, MemorySettings, ToolConfig



class PersonJobNodeData(BaseModel):
    """Data model for Person Job node."""
    person: Optional[str] = Field(description="AI person to use")
    first_only_prompt: str = Field(description="Prompt used only on first execution")
    default_prompt: Optional[str] = Field(description="Default prompt template")
    max_iteration: int = Field(description="Maximum execution iterations")
    memory_profile: Optional[str] = Field(description="Memory profile for conversation context")
    memory_config: Optional[Dict[str, Any]] = Field(description="Deprecated memory configuration")
    memory_settings: Optional[MemorySettings] = Field(description="Custom memory settings")
    tools: Optional[List[ToolConfig]] = Field(description="Tools available to the AI agent")

    class Config:
        extra = "forbid"
        validate_assignment = True