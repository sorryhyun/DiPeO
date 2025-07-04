"""Base file format handler protocol."""

from typing import Any, Protocol, runtime_checkable
from pathlib import Path


@runtime_checkable
class FileFormatHandler(Protocol):
    """Protocol for file format handlers."""
    
    @property
    def supported_extensions(self) -> list[str]:
        """List of supported file extensions (e.g., ['.json', '.JSON'])."""
        ...
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file."""
        ...
    
    def read(self, file_path: Path) -> tuple[Any, str]:
        """Read file and return (parsed_content, raw_content)."""
        ...
    
    async def write(self, file_path: Path, content: Any) -> None:
        """Write content to file."""
        ...
    
    def format_content(self, content: Any) -> str:
        """Format content for writing to file."""
        ...