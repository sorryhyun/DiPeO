"""Plain text file format handler."""

from typing import Any
from pathlib import Path

import aiofiles


class TextHandler:
    """Handler for plain text files."""
    
    @property
    def supported_extensions(self) -> list[str]:
        """List of supported file extensions."""
        # Default handler for all other extensions
        return []
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file."""
        # This is the default handler, so it can handle any file
        return True
    
    def read(self, file_path: Path) -> tuple[str, str]:
        """Read text file and return (parsed_content, raw_content)."""
        content = file_path.read_text(encoding="utf-8")
        # For text files, parsed and raw content are the same
        return content, content
    
    async def write(self, file_path: Path, content: Any) -> None:
        """Write content to text file."""
        formatted = self.format_content(content)
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(formatted)
    
    def format_content(self, content: Any) -> str:
        """Format content as string."""
        return str(content) if not isinstance(content, str) else content