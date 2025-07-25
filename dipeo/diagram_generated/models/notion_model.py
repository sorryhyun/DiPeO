# Auto-generated Pydantic model for notion node

from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field


from dipeo.models.models import NotionOperation


class NotionNodeData(BaseModel):
    """Data model for Notion node."""
    api_key: str = Field(description="Notion API key for authentication")
    database_id: str = Field(description="Notion database ID")
    operation: NotionOperation = Field(description="Operation to perform on the database")
    page_id: Optional[str] = Field(description="Page ID for update operations")

    class Config:
        extra = "forbid"
        validate_assignment = True