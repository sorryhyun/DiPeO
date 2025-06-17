"""Interface for file service."""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class IFileService(ABC):
    """Interface for file operations."""
    
    @abstractmethod
    def read(self, 
            file_id: str, 
            person_id: Optional[str] = None, 
            directory: Optional[str] = None) -> Dict[str, Any]:
        """Read a file from storage."""
        pass
    
    @abstractmethod
    async def write(self,
                   file_id: str,
                   person_id: Optional[str] = None,
                   directory: Optional[str] = None,
                   content: Optional[str] = None) -> Dict[str, Any]:
        """Write content to a file."""
        pass
    
    @abstractmethod
    async def save_file(self, content: bytes, filename: str, target_path: Optional[str] = None) -> Dict[str, Any]:
        """Save uploaded file content."""
        pass