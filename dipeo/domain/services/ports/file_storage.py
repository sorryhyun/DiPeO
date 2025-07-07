"""File storage port for domain layer."""

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class FileStoragePort(Protocol):
    """Port for file storage operations."""

    async def initialize(self) -> None:
        """Initialize the file storage."""
        ...

    def read(
        self, path: str, relative_to: str = "base", encoding: str = "utf-8"
    ) -> str | dict[str, Any]:
        """Read file with automatic format detection."""
        ...

    async def aread(
        self, path: str, relative_to: str = "base", encoding: str = "utf-8"
    ) -> str | dict[str, Any]:
        """Async read file with automatic format detection."""
        ...

    async def write(
        self,
        path: str,
        content: Any,
        relative_to: str = "",
        format: str | None = None,
        encoding: str = "utf-8",
    ) -> str:
        """Write file with automatic format handling."""
        ...

    def list_files(self, path: str, relative_to: str = "base") -> list[Path]:
        """List files in a directory."""
        ...

    def create_directory(self, path: str, relative_to: str = "base") -> Path:
        """Create a directory."""
        ...

    def delete(self, path: str, relative_to: str = "base") -> None:
        """Delete a file or directory."""
        ...

    def exists(self, path: str, relative_to: str = "base") -> bool:
        """Check if a file or directory exists."""
        ...

    def get_size(self, path: str, relative_to: str = "base") -> int:
        """Get the size of a file in bytes."""
        ...

    def save_execution_output(self, execution_id: str, output: dict[str, Any]) -> str:
        """Save execution output to file."""
        ...

    def get_absolute_path(self, path: str, relative_to: str = "base") -> Path:
        """Get absolute path for a given path."""
        ...

    def save_uploaded_file(self, filename: str, content: bytes) -> str:
        """Save an uploaded file."""
        ...

    def get_upload_path(self, filename: str) -> Path:
        """Get the path for an uploaded file."""
        ...
