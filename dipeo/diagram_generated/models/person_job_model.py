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

    max_iteration: int = Field(description="Maximum execution iterations")

    memorize_to: Optional[str] = Field(description="Criteria used to select helpful messages for this task. Empty = memorize all. Special: 'GOLDFISH' for goldfish mode. Comma-separated for multiple criteria.")

    at_most: Optional[float] = Field(description="Select at most N messages to keep (system messages may be preserved in addition).")

    tools: Optional[List[ToolConfig]] = Field(description="Tools available to the AI agent")

    text_format: Optional[str] = Field(description="JSON schema or response format for structured outputs")

    resolved_prompt: Optional[str] = Field(description="Pre-resolved prompt content from compile-time")

    resolved_first_prompt: Optional[str] = Field(description="Pre-resolved first prompt content from compile-time")


    class Config:
        extra = "forbid"
        validate_assignment = True
