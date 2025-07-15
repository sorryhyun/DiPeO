"""Plain text file format handler."""

from pathlib import Path
from typing import Any

import aiofiles


class TextHandler:
    """Handler for plain text files."""
    
    @property
    def supported_extensions(self) -> list[str]:
        """List of supported file extensions.
        
        Returns empty list as this is the default handler for all extensions.
        """
        return []
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file.
        
        This is the default handler, so it can handle any file.
        
        Args:
            file_path: Path to check
            
        Returns:
            Always True as this is the default handler
        """
        return True
    
    def read(self, file_path: Path) -> tuple[str, str]:
        """Read text file and return (parsed_content, raw_content).
        
        For text files, parsed and raw content are the same.
        
        Args:
            file_path: Path to text file
            
        Returns:
            Tuple of (text content, text content)
        """
        content = file_path.read_text(encoding="utf-8")
        # For text files, parsed and raw content are the same
        return content, content
    
    async def write(self, file_path: Path, content: Any) -> None:
        """Write content to text file.
        
        Args:
            file_path: Path to write to
            content: Content to write (will be converted to string)
        """
        formatted = self.format_content(content)
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(formatted)
    
    def format_content(self, content: Any) -> str:
        """Format content as string.
        
        Args:
            content: Content to format
            
        Returns:
            String representation of content
        """
        return str(content) if not isinstance(content, str) else content