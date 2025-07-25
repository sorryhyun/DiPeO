# Auto-generated Pydantic model for json_schema_validator node

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field




class JsonSchemaValidatorNodeData(BaseModel):
    """Data model for JSON Schema Validator node."""
    schema_path: Optional[str] = Field(description="Schema Path configuration")
    schema: Optional[Dict[str, Any]] = Field(description="Schema configuration")
    data_path: Optional[str] = Field(description="Data Path configuration")
    strict_mode: Optional[bool] = Field(description="Strict Mode configuration")
    error_on_extra: Optional[bool] = Field(description="Error On Extra configuration")

    class Config:
        extra = "forbid"
        validate_assignment = True