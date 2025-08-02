







# Auto-generated Pydantic model for db node

from typing import *
from pydantic import *


from dipeo.diagram_generated.enums import *
from dipeo.diagram_generated.integrations import *


class DbNodeData(BaseModel):
    """Data model for Database node."""
    file: Optional[str] = Field(description="File path or array of file paths")
    collection: Optional[str] = Field(description="Database collection name")
    sub_type: DBBlockSubType = Field(description="Database operation type")
    operation: NotionOperation = Field(description="Operation configuration")
    query: Optional[str] = Field(description="Query configuration")
    data: Optional[Dict[str, Any]] = Field(description="Data configuration")
    serialize_json: Optional[bool] = Field(description="Serialize structured data to JSON string (for backward compatibility)")

    class Config:
        extra = "forbid"
        validate_assignment = True