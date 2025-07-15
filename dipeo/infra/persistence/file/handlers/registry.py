"""Registry for file format handlers."""

from pathlib import Path
from typing import Any

from .base import FileFormatHandler
from .csv_handler import CsvHandler
from .docx_handler import DocxHandler
from .json_handler import JsonHandler
from .text_handler import TextHandler
from .yaml_handler import YamlHandler


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
        """Register a new format handler.
        
        Args:
            handler: Handler to register
        """
        self._handlers.append(handler)
    
    def get_handler(self, file_path: Path) -> FileFormatHandler:
        """Get the appropriate handler for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Appropriate handler for the file type
        """
        # Try registered handlers first
        for handler in self._handlers:
            if handler.can_handle(file_path):
                return handler
        
        # Fall back to default text handler
        return self._default_handler
    
    def read_file(self, file_path: Path) -> tuple[Any, str]:
        """Read a file using the appropriate handler.
        
        Args:
            file_path: Path to read from
            
        Returns:
            Tuple of (parsed content, raw content)
        """
        handler = self.get_handler(file_path)
        return handler.read(file_path)
    
    async def write_file(self, file_path: Path, content: Any) -> None:
        """Write content to a file using the appropriate handler.
        
        Args:
            file_path: Path to write to
            content: Content to write
        """
        handler = self.get_handler(file_path)
        await handler.write(file_path, content)
    
    def format_for_extension(self, extension: str, content: Any) -> str:
        """Format content for a specific file extension.
        
        Args:
            extension: File extension (e.g., '.json', '.yaml')
            content: Content to format
            
        Returns:
            Formatted content string
        """
        # Create a dummy path to find the right handler
        dummy_path = Path(f"dummy{extension}")
        handler = self.get_handler(dummy_path)
        return handler.format_content(content)