







# Auto-generated Pydantic model for user_response node

from typing import *
from pydantic import *


from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class UserResponseNodeData(BaseModel):
    """Data model for User Response node."""
    prompt: str = Field(description="Question to ask the user")
    timeout: Optional[int] = Field(description="Response timeout in seconds")

    class Config:
        extra = "forbid"
        validate_assignment = True