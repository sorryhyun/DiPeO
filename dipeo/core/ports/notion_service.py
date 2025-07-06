"""Notion Service port interface."""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class NotionServicePort(Protocol):
    """Port for Notion API operations.
    
    This interface defines the contract for Notion integration,
    supporting page operations, block management, and database queries.
    """

    async def retrieve_page(self, page_id: str, api_key: str) -> Dict[str, Any]:
        """Retrieve a Notion page by ID.
        
        Args:
            page_id: The Notion page ID
            api_key: Notion API key
            
        Returns:
            Page data from Notion API
        """
        ...

    async def list_blocks(self, page_id: str, api_key: str) -> List[Dict[str, Any]]:
        """List all blocks in a Notion page.
        
        Args:
            page_id: The Notion page ID
            api_key: Notion API key
            
        Returns:
            List of block data
        """
        ...

    async def append_blocks(
        self, page_id: str, blocks: List[Dict[str, Any]], api_key: str
    ) -> Dict[str, Any]:
        """Append blocks to a Notion page.
        
        Args:
            page_id: The Notion page ID
            blocks: List of block data to append
            api_key: Notion API key
            
        Returns:
            Response from Notion API
        """
        ...

    async def update_block(
        self, block_id: str, block_data: Dict[str, Any], api_key: str
    ) -> Dict[str, Any]:
        """Update a specific block.
        
        Args:
            block_id: The block ID to update
            block_data: New block data
            api_key: Notion API key
            
        Returns:
            Updated block data
        """
        ...

    async def query_database(
        self,
        database_id: str,
        filter: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None,
        api_key: str = None,
    ) -> Dict[str, Any]:
        """Query a Notion database.
        
        Args:
            database_id: The database ID to query
            filter: Optional filter criteria
            sorts: Optional sort criteria
            api_key: Notion API key
            
        Returns:
            Query results from database
        """
        ...

    async def create_page(
        self,
        parent: Dict[str, Any],
        properties: Dict[str, Any],
        children: Optional[List[Dict]] = None,
        api_key: str = None,
    ) -> Dict[str, Any]:
        """Create a new page in Notion.
        
        Args:
            parent: Parent page or database reference
            properties: Page properties
            children: Optional child blocks
            api_key: Notion API key
            
        Returns:
            Created page data
        """
        ...

    def extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """Extract plain text from Notion blocks.
        
        Args:
            blocks: List of Notion block data
            
        Returns:
            Extracted text content
        """
        ...

    def create_text_block(
        self, text: str, block_type: str = "paragraph"
    ) -> Dict[str, Any]:
        """Create a text block for Notion.
        
        Args:
            text: Text content
            block_type: Type of block (paragraph, heading_1, etc.)
            
        Returns:
            Formatted block data
        """
        ...