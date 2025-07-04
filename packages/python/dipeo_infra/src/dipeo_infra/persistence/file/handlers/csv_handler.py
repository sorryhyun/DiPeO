"""CSV file format handler."""

import csv
import io
from typing import Any, Dict, List
from pathlib import Path

import aiofiles


class CsvHandler:
    """Handler for CSV files."""
    
    @property
    def supported_extensions(self) -> list[str]:
        """List of supported file extensions."""
        return [".csv", ".CSV"]
    
    def can_handle(self, file_path: Path) -> bool:
        """Check if this handler can process the given file."""
        return file_path.suffix.lower() == ".csv"
    
    def read(self, file_path: Path) -> tuple[List[Dict[str, Any]], str]:
        """Read CSV file and return (parsed_content, raw_content)."""
        with open(file_path, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            content = list(reader)
            
        # Re-read for raw content
        raw = file_path.read_text(encoding="utf-8")
        return content, raw
    
    async def write(self, file_path: Path, content: Any) -> None:
        """Write content to CSV file."""
        formatted = self.format_content(content)
        async with aiofiles.open(file_path, "w", encoding="utf-8") as f:
            await f.write(formatted)
    
    def format_content(self, content: Any) -> str:
        """Format content as CSV string."""
        if isinstance(content, str):
            # If already a string, return as-is
            return content
        
        if not isinstance(content, list):
            raise ValueError("CSV content must be a list of dictionaries")
        
        if not content:
            return ""
        
        # Get all keys
        all_keys = set()
        for row in content:
            if isinstance(row, dict):
                all_keys.update(row.keys())
        
        fieldnames = sorted(all_keys)
        
        # Write to string
        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(content)
        
        return output.getvalue()