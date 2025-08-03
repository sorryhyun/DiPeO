import logging
from typing import Any

from notion_client import Client

from dipeo.core import BaseService, ExecutionError

logger = logging.getLogger(__name__)


class NotionAPIService(BaseService):
    def __init__(self):
        super().__init__()
        self._clients: dict[str, Client] = {}

    async def initialize(self) -> None:
        pass

    def _get_client(self, api_key: str) -> Client:
        if api_key not in self._clients:
            self._clients[api_key] = Client(auth=api_key)
        return self._clients[api_key]

    async def retrieve_page(self, page_id: str, api_key: str) -> dict[str, Any]:
        try:
            client = self._get_client(api_key)
            return client.pages.retrieve(page_id=page_id)
        except Exception as e:
            logger.error(f"Failed to retrieve Notion page: {e}")
            raise ExecutionError(f"Notion API error: {e!s}")

    async def list_blocks(self, page_id: str, api_key: str) -> list[dict[str, Any]]:
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
            raise ExecutionError(f"Notion API error: {e!s}")

    async def append_blocks(
        self, page_id: str, blocks: list[dict[str, Any]], api_key: str
    ) -> dict[str, Any]:
        try:
            client = self._get_client(api_key)
            return client.blocks.children.append(block_id=page_id, children=blocks)
        except Exception as e:
            logger.error(f"Failed to append Notion blocks: {e}")
            raise ExecutionError(f"Notion API error: {e!s}")

    async def update_block(
        self, block_id: str, block_data: dict[str, Any], api_key: str
    ) -> dict[str, Any]:
        try:
            client = self._get_client(api_key)
            return client.blocks.update(block_id=block_id, **block_data)
        except Exception as e:
            logger.error(f"Failed to update Notion block: {e}")
            raise ExecutionError(f"Notion API error: {e!s}")

    async def query_database(
        self,
        database_id: str,
        filter: dict | None = None,
        sorts: list | None = None,
        api_key: str | None = None,
    ) -> list[dict[str, Any]]:
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
            raise ExecutionError(f"Notion API error: {e!s}")

    async def create_page(
        self,
        parent: dict[str, Any],
        properties: dict[str, Any],
        children: list[dict] | None = None,
        api_key: str | None = None,
    ) -> dict[str, Any]:
        try:
            client = self._get_client(api_key)
            page_data = {"parent": parent, "properties": properties}
            if children:
                page_data["children"] = children

            return client.pages.create(**page_data)
        except Exception as e:
            logger.error(f"Failed to create Notion page: {e}")
            raise ExecutionError(f"Notion API error: {e!s}")

    def extract_text_from_blocks(self, blocks: list[dict[str, Any]]) -> str:
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
    ) -> dict[str, Any]:
        return {
            "object": "block",
            "type": block_type,
            block_type: {"rich_text": [{"type": "text", "text": {"content": text}}]},
        }