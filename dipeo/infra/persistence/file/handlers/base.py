"""Base file format handler protocol."""

from pathlib import Path
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class FileFormatHandler(Protocol):
    """Protocol for file format handlers."""
    
    @property
    def supported_extensions(self) -> list[str]:
        """List of supported file extensions (e.g., ['.json', '.JSON'])."""
        ...
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file.
        
        Args:
            file_path: Path to the file to check
            
        Returns:
            True if handler can process the file
        """
        ...
    
    def read(self, file_path: Path) -> tuple[Any, str]:
        """Read file and return (parsed_content, raw_content).
        
        Args:
            file_path: Path to the file to read
            
        Returns:
            Tuple of (parsed content, raw string content)
        """
        ...
    
    async def write(self, file_path: Path, content: Any) -> None:
        """Write content to file.
        
        Args:
            file_path: Path to write to
            content: Content to write
        """
        ...
    
    def format_content(self, content: Any) -> str:
        """Format content for writing to file.
        
        Args:
            content: Content to format
            
        Returns:
            Formatted string content
        """
        ...