"""Registry for file format handlers."""

from pathlib import Path
from typing import Any, Optional

from .base import FileFormatHandler
from .json_handler import JsonHandler
from .yaml_handler import YamlHandler
from .csv_handler import CsvHandler
from .docx_handler import DocxHandler
from .text_handler import TextHandler


class FormatHandlerRegistry:
    """Registry for managing file format handlers."""
    
    def __init__(self):
        """Initialize the registry with default handlers."""
        self._handlers: list[FileFormatHandler] = []
        self._default_handler = TextHandler()
        
        # Register default handlers
        self.register(JsonHandler())
        self.register(YamlHandler())
        self.register(CsvHandler())
        self.register(DocxHandler())
    
    def register(self, handler: FileFormatHandler) -> None:
        """Register a new format handler."""
        self._handlers.append(handler)
    
    def get_handler(self, file_path: Path) -> FileFormatHandler:
        """Get the appropriate handler for a file."""
        # Try registered handlers first
        for handler in self._handlers:
            if handler.can_handle(file_path):
                return handler
        
        # Fall back to default text handler
        return self._default_handler
    
    def read_file(self, file_path: Path) -> tuple[Any, str]:
        """Read a file using the appropriate handler."""
        handler = self.get_handler(file_path)
        return handler.read(file_path)
    
    async def write_file(self, file_path: Path, content: Any) -> None:
        """Write content to a file using the appropriate handler."""
        handler = self.get_handler(file_path)
        await handler.write(file_path, content)
    
    def format_for_extension(self, extension: str, content: Any) -> str:
        """Format content for a specific file extension."""
        # Create a dummy path to find the right handler
        dummy_path = Path(f"dummy{extension}")
        handler = self.get_handler(dummy_path)
        return handler.format_content(content)