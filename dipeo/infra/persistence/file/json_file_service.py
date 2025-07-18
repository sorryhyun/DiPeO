"""JSON file operations service."""

import json
import logging
from typing import Any

from dipeo.core import FileOperationError, handle_file_operation

logger = logging.getLogger(__name__)


class JsonFileService:
    """Service for JSON-specific file operations."""
    
    def __init__(self, file_service):
        """Initialize with a file service dependency.
        
        Args:
            file_service: Core file service for basic operations
        """
        self.file_service = file_service
    
    @handle_file_operation("read_json")
    async def read_json(
        self,
        file_path: str,
        encoding: str = "utf-8",
    ) -> dict[str, Any] | list[Any]:
        """Read and parse JSON file.
        
        Args:
            file_path: Path to JSON file
            encoding: File encoding
            
        Returns:
            Parsed JSON data
            
        Raises:
            FileOperationError: On read or parse failures
        """
        try:
            result = self.file_service.read(file_path)
            if not result["success"]:
                raise FileOperationError("read_json", file_path, result.get('error', 'Unknown error'))
            
            # Parse JSON
            try:
                return json.loads(result["raw_content"])
            except json.JSONDecodeError as e:
                raise FileOperationError("read_json", file_path, f"Invalid JSON content: {e}")
            
        except Exception as e:
            if isinstance(e, FileOperationError):
                raise
            raise FileOperationError("read_json", file_path, str(e))
    
    @handle_file_operation("write_json")
    async def write_json(
        self,
        file_path: str,
        data: dict[str, Any] | list[Any],
        indent: int = 2,
        sort_keys: bool = True,
        encoding: str = "utf-8",
        create_backup: bool = False,
    ) -> None:
        """Write data as JSON to file.
        
        Args:
            file_path: Target file path
            data: Data to write
            indent: JSON indentation
            sort_keys: Whether to sort keys
            encoding: File encoding
            create_backup: Whether to create backup
            
        Raises:
            FileOperationError: On write failures
        """
        try:
            # Format JSON
            content = json.dumps(data, indent=indent, sort_keys=sort_keys, ensure_ascii=False)
            
            # Write to file
            result = await self.file_service.write(
                file_id=file_path,
                content=content,
            )
            
            if not result["success"]:
                raise FileOperationError("write_json", file_path, result.get('error', 'Unknown error'))
            
        except Exception as e:
            if isinstance(e, FileOperationError):
                raise
            raise FileOperationError("write_json", file_path, str(e))
    
    async def update_json(
        self,
        file_path: str,
        updates: dict[str, Any],
        merge_strategy: str = "shallow"
    ) -> None:
        """Update JSON file with new data.
        
        Args:
            file_path: Path to JSON file
            updates: Data to merge into existing JSON
            merge_strategy: How to merge data ("shallow" or "deep")
            
        Raises:
            FileOperationError: On read/write failures
        """
        # Read existing data
        existing_data = await self.read_json(file_path)
        
        # Ensure we're working with a dict
        if not isinstance(existing_data, dict):
            raise FileOperationError(
                "update_json", 
                file_path, 
                "Cannot update non-dictionary JSON data"
            )
        
        # Merge data based on strategy
        if merge_strategy == "shallow":
            existing_data.update(updates)
        elif merge_strategy == "deep":
            existing_data = self._deep_merge(existing_data, updates)
        else:
            raise ValueError(f"Unknown merge strategy: {merge_strategy}")
        
        # Write back
        await self.write_json(file_path, existing_data)
    
    def _deep_merge(self, base: dict, updates: dict) -> dict:
        """Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            updates: Updates to apply
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in updates.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result