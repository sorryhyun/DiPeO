"""File Service port interface."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class FileServicePort(Protocol):
    """Port for file operations.
    
    Interface for file storage implementations supporting
    JSON, YAML, CSV, TXT, and other file types.
    """

    def read(
        self,
        file_id: str,
        person_id: str | None = None,
        directory: str | None = None,
    ) -> dict[str, Any]:
        ...

    async def write(
        self,
        file_id: str,
        person_id: str | None = None,
        directory: str | None = None,
        content: str | None = None,
    ) -> dict[str, Any]:
        ...

    async def save_file(
        self, content: bytes, filename: str, target_path: str | None = None
    ) -> dict[str, Any]:
        ...