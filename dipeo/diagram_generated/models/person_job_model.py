# Auto-generated Pydantic model for person_job node

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


from dipeo.diagram_generated.domain_models import PersonID, MemorySettings, ToolConfig



class PersonJobNodeData(BaseModel):
    """Data model for Person Job node."""
    person: Optional[str] = Field(description="Person configuration")
    first_only_prompt: str = Field(description="First Only Prompt configuration")
    default_prompt: Optional[str] = Field(description="Default Prompt configuration")
    max_iteration: float = Field(description="Max Iteration configuration")
    memory_config: Optional[Dict[str, Any]] = Field(description="Memory Config configuration (deprecated - use memory_settings)")
    memory_settings: Optional[Dict[str, Any]] = Field(description="Memory Settings configuration")
    tools: Optional[List[Any]] = Field(description="Tools configuration")

    class Config:
        extra = "forbid"
        validate_assignment = True