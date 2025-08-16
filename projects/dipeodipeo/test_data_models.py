"""
Pydantic models for test data generation via LLM.
"""

from typing import List, Dict, Optional, Union, Literal
from pydantic import BaseModel, Field, ConfigDict
from enum import Enum


class DataType(str, Enum):
    """Supported data types for test data generation."""
    CSV = "csv"
    JSON = "json"
    YAML = "yaml"


class FieldDefinition(BaseModel):
    """Definition of a field in the test data."""
    model_config = ConfigDict(extra='forbid')
    
    name: str = Field(description="Field name")
    type: Literal["string", "integer", "float", "boolean", "date", "datetime", "email", "url", "uuid"] = Field(
        description="Data type of the field"
    )
    nullable: bool = Field(default=False, description="Whether the field can have null values")
    unique: bool = Field(default=False, description="Whether values should be unique")
    min_value: Optional[float] = Field(default=None, description="Minimum value for numeric fields")
    max_value: Optional[float] = Field(default=None, description="Maximum value for numeric fields")
    pattern: Optional[str] = Field(default=None, description="Regex pattern for string fields")
    choices: Optional[List[Union[str, int, float, bool]]] = Field(default=None, description="List of possible values (strings, numbers, or booleans)")
    description: Optional[str] = Field(default=None, description="Field description for context")


class TestDataSpecification(BaseModel):
    """Specification for generating test data."""
    model_config = ConfigDict(extra='forbid')
    
    format: DataType = Field(default=DataType.CSV, description="Output format for the test data")
    num_rows: int = Field(default=10, ge=1, le=100, description="Number of rows to generate")
    fields: List[FieldDefinition] = Field(description="Field definitions for the test data")
    include_headers: bool = Field(default=True, description="Whether to include headers in CSV output")
    description: str = Field(description="Description of what this test data represents")


class GeneratedTestData(BaseModel):
    """Generated test data with metadata."""
    model_config = ConfigDict(extra='forbid')
    
    specification: TestDataSpecification = Field(description="The specification used to generate this data")
    csv_content: str = Field(description="CSV formatted content ready to save")
    row_count: int = Field(description="Number of data rows generated")
    field_count: int = Field(description="Number of fields per row")


class Response(BaseModel):
    """Response containing the generated test data."""
    model_config = ConfigDict(extra='forbid')
    
    test_data: GeneratedTestData = Field(description="The generated test data with CSV content")
    summary: str = Field(description="Brief summary of what was generated")

