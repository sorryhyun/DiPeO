







# Auto-generated Pydantic model for endpoint node

from typing import *
from pydantic import *


from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class EndpointNodeData(BaseModel):
    """Data model for End Node node."""
    save_to_file: bool = Field(description="Save results to file")
    file_name: Optional[str] = Field(description="Output filename")

    class Config:
        extra = "forbid"
        validate_assignment = True