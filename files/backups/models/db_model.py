# Auto-generated Pydantic model for db node

from typing import *

from pydantic import *

from ..enums import *
from ..integrations import *


class DbNodeData(BaseModel):
    """Data model for Database node."""

    file: Optional[Union[str, List[str]]] = Field(description="File path or array of file paths")

    collection: Optional[str] = Field(description="Database collection name")

    sub_type: DBBlockSubType = Field(description="Database operation type")

    operation: str = Field(description="Operation configuration")

    query: Optional[str] = Field(description="Query configuration")

    data: Optional[Dict[str, Any]] = Field(description="Data configuration")

    serialize_json: Optional[bool] = Field(
        description="Serialize structured data to JSON string (for backward compatibility)"
    )

    format: Optional[str] = Field(description="Data format (json, yaml, csv, text, etc.)")

    class Config:
        extra = "forbid"
        validate_assignment = True
