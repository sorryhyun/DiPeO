# Auto-generated Pydantic model for person_batch_job node

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field




class PersonBatchJobNodeData(BaseModel):
    """Data model for Person Batch Job node."""
    person: Optional[str] = Field(description="Person configuration for AI model")
    batch_key: str = Field(description="Key containing the array to iterate over")
    prompt: str = Field(description="Prompt template for each batch item")

    class Config:
        extra = "forbid"
        validate_assignment = True