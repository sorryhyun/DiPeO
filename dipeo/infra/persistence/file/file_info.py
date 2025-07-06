"""File information model."""

from typing import Any, Optional
from pydantic import BaseModel


class FileInfo(BaseModel):
    """Information about a file."""
    id: str
    name: str
    path: str
    format: Optional[str] = None
    extension: str
    modified: str
    size: int

    def to_dict(self) -> dict[str, Any]:
        """Convert FileInfo to dictionary."""
        return self.model_dump()