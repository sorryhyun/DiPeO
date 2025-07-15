"""Notion Service port interface."""

from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class NotionServicePort(Protocol):
    """Port for Notion API operations.
    
    Interface for Notion integration with page operations,
    block management, and database queries.
    """

    async def retrieve_page(self, page_id: str, api_key: str) -> dict[str, Any]:
        ...

    async def list_blocks(self, page_id: str, api_key: str) -> list[dict[str, Any]]:
        ...

    async def append_blocks(
        self, page_id: str, blocks: list[dict[str, Any]], api_key: str
    ) -> dict[str, Any]:
        ...

    async def update_block(
        self, block_id: str, block_data: dict[str, Any], api_key: str
    ) -> dict[str, Any]:
        ...

    async def query_database(
        self,
        database_id: str,
        filter: dict | None = None,
        sorts: list[dict] | None = None,
        api_key: str = None,
    ) -> dict[str, Any]:
        ...

    async def create_page(
        self,
        parent: dict[str, Any],
        properties: dict[str, Any],
        children: list[dict] | None = None,
        api_key: str = None,
    ) -> dict[str, Any]:
        ...

    def extract_text_from_blocks(self, blocks: list[dict[str, Any]]) -> str:
        ...

    def create_text_block(
        self, text: str, block_type: str = "paragraph"
    ) -> dict[str, Any]:
        ...