"""JSON file format handler."""

import json
from pathlib import Path
from typing import Any

import aiofiles


class JsonHandler:
    """Handler for JSON files."""
    
    @property
    def supported_extensions(self) -> list[str]:
        """List of supported file extensions."""
        return [".json", ".JSON"]
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if this is a JSON file
        """
        return file_path.suffix.lower() == ".json"
    
    def read(self, file_path: Path) -> tuple[Any, str]:
        """Read JSON file and return (parsed_content, raw_content).
        
        Args:
            file_path: Path to JSON file
            
        Returns:
            Tuple of (parsed JSON object, raw JSON string)
        """
        with open(file_path, encoding="utf-8") as f:
            content = json.load(f)
            raw = json.dumps(content, ensure_ascii=False)
            return content, raw
    
    async def write(self, file_path: Path, content: Any) -> None:
        """Write content to JSON file.
        
        Args:
            file_path: Path to write to
            content: Content to write (will be JSON serialized)
        """
        formatted = self.format_content(content)
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(formatted)
    
    def format_content(self, content: Any) -> str:
        """Format content as JSON string.
        
        Args:
            content: Content to format
            
        Returns:
            Formatted JSON string
        """
        if isinstance(content, str):
            # If already a string, parse and re-format for consistency
            try:
                parsed = json.loads(content)
                return json.dumps(parsed, indent=2, ensure_ascii=False)
            except json.JSONDecodeError:
                # If not valid JSON, write as-is
                return content
        return json.dumps(content, indent=2, ensure_ascii=False)