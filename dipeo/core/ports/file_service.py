"""File Service port interface."""

from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class FileServicePort(Protocol):
    """Port for file operations.
    
    This interface defines the contract for file storage implementations,
    supporting various file types (JSON, YAML, CSV, TXT, etc.).
    """

    def read(
        self,
        file_id: str,
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Read a file and return its contents.
        
        Args:
            file_id: Identifier or path of the file to read
            person_id: Optional person context for file resolution
            directory: Optional directory override
            
        Returns:
            Dictionary with file content and metadata
        """
        ...

    async def write(
        self,
        file_id: str,
        person_id: Optional[str] = None,
        directory: Optional[str] = None,
        content: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Write content to a file.
        
        Args:
            file_id: Identifier or path of the file to write
            person_id: Optional person context for file resolution
            directory: Optional directory override
            content: Content to write to the file
            
        Returns:
            Dictionary with write operation result
        """
        ...

    async def save_file(
        self, content: bytes, filename: str, target_path: Optional[str] = None
    ) -> Dict[str, Any]:
        """Save binary content to a file.
        
        Args:
            content: Binary content to save
            filename: Name of the file
            target_path: Optional target directory path
            
        Returns:
            Dictionary with saved file information
        """
        ...