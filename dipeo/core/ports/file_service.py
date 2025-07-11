"""File Service port interface."""

from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class FileServicePort(Protocol):
    """Port for file operations.
    
    Interface for file storage implementations supporting
    JSON, YAML, CSV, TXT, and other file types.
    """

    def read(
        self,
        file_id: str,
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        ...

    async def write(
        self,
        file_id: str,
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        ...

    async def save_file(
        self, content: bytes, filename: str, target_path: Optional[str] = None
    ) -> Dict[str, Any]:
        ...