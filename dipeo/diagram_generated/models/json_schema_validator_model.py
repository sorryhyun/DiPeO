# Auto-generated Pydantic model for json_schema_validator node

from typing import *
from pydantic import *


from ..enums import *
from ..integrations import *


class JsonSchemaValidatorNodeData(BaseModel):
    """Data model for JSON Schema Validator node."""
    schema_path: Optional[str] = Field(description="Path to JSON schema file")
    schema: Optional[Dict[str, Any]] = Field(description="Inline JSON schema")
    data_path: Optional[str] = Field(description="Data Path configuration")
    strict_mode: Optional[bool] = Field(description="Strict Mode configuration")
    error_on_extra: Optional[bool] = Field(description="Error On Extra configuration")

    class Config:
        extra = "forbid"
        validate_assignment = True