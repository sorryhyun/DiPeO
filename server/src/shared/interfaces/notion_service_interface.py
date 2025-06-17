"""Interface for Notion service."""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional


class INotionService(ABC):
    """Interface for Notion API operations."""
    
    @abstractmethod
    async def retrieve_page(self, page_id: str, api_key: str) -> Dict[str, Any]:
        """Retrieve a Notion page by ID."""
        pass
    
    @abstractmethod
    async def list_blocks(self, page_id: str, api_key: str) -> List[Dict[str, Any]]:
        """List all blocks in a Notion page."""
        pass
    
    @abstractmethod
    async def append_blocks(self, page_id: str, blocks: List[Dict[str, Any]], api_key: str) -> Dict[str, Any]:
        """Append blocks to a Notion page."""
        pass
    
    @abstractmethod
    async def update_block(self, block_id: str, block_data: Dict[str, Any], api_key: str) -> Dict[str, Any]:
        """Update a specific block in Notion."""
        pass
    
    @abstractmethod
    async def query_database(self, database_id: str, filter: Optional[Dict] = None, 
                           sorts: Optional[List[Dict]] = None, api_key: str = None) -> Dict[str, Any]:
        """Query a Notion database."""
        pass
    
    @abstractmethod
    async def create_page(self, parent: Dict[str, Any], properties: Dict[str, Any], 
                         children: Optional[List[Dict]] = None, api_key: str = None) -> Dict[str, Any]:
        """Create a new page in Notion."""
        pass
    
    @abstractmethod
    def extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """Extract plain text from Notion blocks."""
        pass
    
    @abstractmethod
    def create_text_block(self, text: str, block_type: str = "paragraph") -> Dict[str, Any]:
        """Create a text block for Notion."""
        pass