"""File information model."""

from typing import Any

from pydantic import BaseModel


class FileInfo(BaseModel):
    """Information about a file."""
    id: str
    name: str
    path: str
    format: str | None = None
    extension: str
    modified: str
    size: int

    def to_dict(self) -> dict[str, Any]:
        """Convert FileInfo to dictionary."""
        return self.model_dump()