import logging
from typing import Any, Dict, List, Optional

from notion_client import Client

from dipeo_server.core.base import BaseService
from dipeo_server.core.exceptions import DiagramExecutionError

logger = logging.getLogger(__name__)


class NotionService(BaseService):
    def __init__(self):
        super().__init__()
        self._clients: Dict[str, Client] = {}

    def _get_client(self, api_key: str) -> Client:
        if api_key not in self._clients:
            self._clients[api_key] = Client(auth=api_key)
        return self._clients[api_key]

    async def retrieve_page(self, page_id: str, api_key: str) -> Dict[str, Any]:
        """Retrieve page metadata"""
        try:
            client = self._get_client(api_key)
            response = client.pages.retrieve(page_id=page_id)
            return response
        except Exception as e:
            logger.error(f"Failed to retrieve Notion page: {e}")
            raise DiagramExecutionError(f"Notion API error: {e!s}")

    async def list_blocks(self, page_id: str, api_key: str) -> List[Dict[str, Any]]:
        """List all blocks in a page"""
        try:
            client = self._get_client(api_key)
            all_blocks = []
            start_cursor = None
            has_more = True

            while has_more:
                response = client.blocks.children.list(
                    block_id=page_id, start_cursor=start_cursor, page_size=50
                )
                all_blocks.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")

            return all_blocks
        except Exception as e:
            logger.error(f"Failed to list Notion blocks: {e}")
            raise DiagramExecutionError(f"Notion API error: {e!s}")

    async def append_blocks(
        self, page_id: str, blocks: List[Dict[str, Any]], api_key: str
    ) -> Dict[str, Any]:
        """Append blocks to a page"""
        try:
            client = self._get_client(api_key)
            response = client.blocks.children.append(block_id=page_id, children=blocks)
            return response
        except Exception as e:
            logger.error(f"Failed to append Notion blocks: {e}")
            raise DiagramExecutionError(f"Notion API error: {e!s}")

    async def update_block(
        self, block_id: str, block_data: Dict[str, Any], api_key: str
    ) -> Dict[str, Any]:
        """Update a block"""
        try:
            client = self._get_client(api_key)
            response = client.blocks.update(block_id=block_id, **block_data)
            return response
        except Exception as e:
            logger.error(f"Failed to update Notion block: {e}")
            raise DiagramExecutionError(f"Notion API error: {e!s}")

    async def query_database(
        self,
        database_id: str,
        filter: Optional[Dict] = None,
        sorts: Optional[List] = None,
        api_key: str = None,
    ) -> List[Dict[str, Any]]:
        """Query a Notion database"""
        try:
            client = self._get_client(api_key)
            all_results = []
            start_cursor = None
            has_more = True

            query_params = {"database_id": database_id, "page_size": 100}
            if filter:
                query_params["filter"] = filter
            if sorts:
                query_params["sorts"] = sorts

            while has_more:
                if start_cursor:
                    query_params["start_cursor"] = start_cursor

                response = client.databases.query(**query_params)
                all_results.extend(response.get("results", []))
                has_more = response.get("has_more", False)
                start_cursor = response.get("next_cursor")

            return all_results
        except Exception as e:
            logger.error(f"Failed to query Notion database: {e}")
            raise DiagramExecutionError(f"Notion API error: {e!s}")

    async def create_page(
        self,
        parent: Dict[str, Any],
        properties: Dict[str, Any],
        children: Optional[List[Dict]] = None,
        api_key: str = None,
    ) -> Dict[str, Any]:
        """Create a new page in Notion"""
        try:
            client = self._get_client(api_key)
            page_data = {"parent": parent, "properties": properties}
            if children:
                page_data["children"] = children

            response = client.pages.create(**page_data)
            return response
        except Exception as e:
            logger.error(f"Failed to create Notion page: {e}")
            raise DiagramExecutionError(f"Notion API error: {e!s}")

    def extract_text_from_blocks(self, blocks: List[Dict[str, Any]]) -> str:
        """Extract plain text from Notion blocks"""
        text_parts = []

        for block in blocks:
            block_type = block.get("type")
            if block_type in [
                "paragraph",
                "heading_1",
                "heading_2",
                "heading_3",
                "bulleted_list_item",
                "numbered_list_item",
                "to_do",
                "toggle",
                "quote",
            ]:
                block_content = block.get(block_type, {})
                rich_text = block_content.get("rich_text", [])
                for text_item in rich_text:
                    if text_item.get("type") == "text":
                        text_parts.append(text_item.get("text", {}).get("content", ""))

        return "\n".join(text_parts)

    def create_text_block(
        self, text: str, block_type: str = "paragraph"
    ) -> Dict[str, Any]:
        """Create a text block for Notion"""
        return {
            "object": "block",
            "type": block_type,
            block_type: {"rich_text": [{"type": "text", "text": {"content": text}}]},
        }
