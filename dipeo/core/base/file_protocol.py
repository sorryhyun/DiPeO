"""Unified file service protocol for DiPeO."""

from typing import Any, Dict, List, Optional, Protocol, Union, runtime_checkable


@runtime_checkable
class FileServiceProtocol(Protocol):
    """Unified protocol for all file operations in DiPeO.
    
    This protocol consolidates file operations from multiple services:
    - Basic file I/O (read, write, save)
    - Validation and error handling
    - JSON operations
    - File listing and filtering
    - Backup and copy operations
    """
    
    # Basic file operations (from SupportsFile)
    def read(
        self,
        file_id: str,
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]: 
        """Read a file and return metadata and content."""
        ...
    
    async def write(
        self,
        file_id: str,
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Dict[str, Any]: 
        """Write content to a file."""
        ...
    
    async def save_file(
        self, content: bytes, filename: str, target_path: Optional[str] = None
    ) -> Dict[str, Any]: 
        """Save binary content to a file."""
        ...
    
    # Enhanced operations with validation
    async def read_with_validation(
        self,
        path: str,
        allowed_extensions: Optional[List[str]] = None,
        max_size_mb: float = 10.0,
        encoding: str = "utf-8",
    ) -> str:
        """Read file with validation and error handling."""
        ...
    
    async def write_with_backup(
        self,
        path: str,
        content: str,
        create_backup: bool = True,
        backup_suffix: str = ".bak",
    ) -> None:
        """Write file with optional backup of existing file."""
        ...
    
    async def append_with_timestamp(
        self,
        path: str,
        content: str,
        separator: str = "\n",
        add_timestamp: bool = True,
    ) -> None:
        """Append content to file with optional timestamp."""
        ...
    
    # JSON operations
    async def read_json_safe(
        self,
        path: str,
        default: Optional[Union[Dict[str, Any], List[Any]]] = None,
    ) -> Union[Dict[str, Any], List[Any]]:
        """Safely read JSON file with error handling."""
        ...
    
    async def write_json_pretty(
        self,
        path: str,
        data: Union[Dict[str, Any], List[Any]],
        indent: int = 2,
        sort_keys: bool = True,
    ) -> None:
        """Write JSON file with pretty formatting."""
        ...
    
    # File listing and filtering
    async def list_files_filtered(
        self,
        directory: str,
        extensions: Optional[List[str]] = None,
        pattern: Optional[str] = None,
        recursive: bool = False,
    ) -> List[str]:
        """List files in directory with filtering."""
        ...
    
    # File operations
    async def copy_with_validation(
        self,
        source: str,
        destination: str,
        overwrite: bool = False,
        validate_checksum: bool = False,
    ) -> None:
        """Copy file with validation."""
        ...
    
    # Utility methods
    async def file_exists(self, path: str) -> bool:
        """Check if file exists."""
        ...
    
    async def get_file_size(self, path: str) -> int:
        """Get file size in bytes."""
        ...