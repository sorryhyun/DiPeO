"""Notion Service port interface."""

from typing import Any, Dict, List, Optional, Protocol, runtime_checkable


@runtime_checkable
class NotionServicePort(Protocol):
    """Port for Notion API operations.
    
    Interface for Notion integration with page operations,
    block management, and database queries.
    """

    async def retrieve_page(self, page_id: str, api_key: str) -> Dict[str, Any]:
        ...

    async def list_blocks(self, page_id: str, api_key: str) -> List[Dict[str, Any]]:
        ...

    async def append_blocks(
        self, page_id: str, blocks: List[Dict[str, Any]], api_key: str
    ) -> Dict[str, Any]:
        ...

    async def update_block(
        self, block_id: str, block_data: Dict[str, Any], api_key: str
    ) -> Dict[str, Any]:
        ...

    async def query_database(
        self,
        database_id: str,
        filter: Optional[Dict] = None,
        sorts: Optional[List[Dict]] = None,
        api_key: str = None,
    ) -> Dict[str, Any]:
        ...

    async def create_page(
        self,
        parent: Dict[str, Any],
        properties: Dict[str, Any],
        children: Optional[List[Dict]] = None,
        api_key: str = None,
    ) -> Dict[str, Any]:
        ...

    def extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        ...

    def create_text_block(
        self, text: str, block_type: str = "paragraph"
    ) -> Dict[str, Any]:
        ...