"""Notion provider for integrated API service."""

import logging
from typing import Any, Optional

from notion_client import Client

from dipeo.core import ExecutionError
from .base_provider import BaseApiProvider

logger = logging.getLogger(__name__)


class NotionProvider(BaseApiProvider):
    """Notion API provider implementation."""

    SUPPORTED_OPERATIONS = [
        "create_page",
        "update_page",
        "read_page",
        "delete_page",
        "create_database",
        "query_database",
        "update_database"
    ]

    def __init__(self):
        super().__init__("notion", self.SUPPORTED_OPERATIONS)
        self._clients: dict[str, Client] = {}

    async def initialize(self) -> None:
        """Initialize the Notion provider."""
        await super().initialize()

    def _get_client(self, api_key: str) -> Client:
        """Get or create a Notion client for the given API key."""
        if api_key not in self._clients:
            self._clients[api_key] = Client(auth=api_key)
        return self._clients[api_key]

    async def _execute_operation(
        self,
        operation: str,
        config: dict[str, Any],
        resource_id: Optional[str],
        api_key: str,
        timeout: float
    ) -> dict[str, Any]:
        """Execute Notion-specific operations."""
        
        client = self._get_client(api_key)
        
        try:
            if operation == "read_page":
                if not resource_id:
                    raise ValueError("page_id required for read_page operation")
                result = await self._retrieve_page(client, resource_id)
                
            elif operation == "create_page":
                parent = config.get("parent", {})
                properties = config.get("properties", {})
                children = config.get("children")
                result = await self._create_page(
                    client=client,
                    parent=parent,
                    properties=properties,
                    children=children
                )
                
            elif operation == "update_page":
                if not resource_id:
                    raise ValueError("page_id required for update_page operation")
                blocks = config.get("blocks", [])
                if blocks:
                    result = await self._append_blocks(client, resource_id, blocks)
                else:
                    raise ValueError("update_page requires blocks to append")
                    
            elif operation == "query_database":
                if not resource_id:
                    raise ValueError("database_id required for query_database operation")
                filter_query = config.get("filter")
                sorts = config.get("sorts")
                result = await self._query_database(
                    client=client,
                    database_id=resource_id,
                    filter=filter_query,
                    sorts=sorts
                )
                
            elif operation in ["delete_page", "create_database", "update_database"]:
                raise NotImplementedError(f"Operation '{operation}' not yet implemented")
                
            else:
                raise ValueError(f"Unknown operation: {operation}")

            return self._build_success_response(result, operation)
            
        except Exception as e:
            logger.error(f"Failed to execute Notion operation '{operation}': {e}")
            raise ExecutionError(f"Notion API error: {e!s}")

    async def _retrieve_page(self, client: Client, page_id: str) -> dict[str, Any]:
        """Retrieve a Notion page."""
        try:
            return client.pages.retrieve(page_id=page_id)
        except Exception as e:
            logger.error(f"Failed to retrieve Notion page: {e}")
            raise ExecutionError(f"Notion API error: {e!s}")

    async def _list_blocks(self, client: Client, page_id: str) -> list[dict[str, Any]]:
        """List all blocks in a Notion page."""
        try:
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

    async def _append_blocks(
        self, client: Client, page_id: str, blocks: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """Append blocks to a Notion page."""
        try:
            return client.blocks.children.append(block_id=page_id, children=blocks)
        except Exception as e:
            logger.error(f"Failed to append Notion blocks: {e}")
            raise ExecutionError(f"Notion API error: {e!s}")

    async def _update_block(
        self, client: Client, block_id: str, block_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Update a Notion block."""
        try:
            return client.blocks.update(block_id=block_id, **block_data)
        except Exception as e:
            logger.error(f"Failed to update Notion block: {e}")
            raise ExecutionError(f"Notion API error: {e!s}")

    async def _query_database(
        self,
        client: Client,
        database_id: str,
        filter: dict | None = None,
        sorts: list | None = None,
    ) -> list[dict[str, Any]]:
        """Query a Notion database."""
        try:
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

    async def _create_page(
        self,
        client: Client,
        parent: dict[str, Any],
        properties: dict[str, Any],
        children: list[dict] | None = None,
    ) -> dict[str, Any]:
        """Create a new Notion page."""
        try:
            page_data = {"parent": parent, "properties": properties}
            if children:
                page_data["children"] = children

            return client.pages.create(**page_data)
        except Exception as e:
            logger.error(f"Failed to create Notion page: {e}")
            raise ExecutionError(f"Notion API error: {e!s}")

    def extract_text_from_blocks(self, blocks: list[dict[str, Any]]) -> str:
        """Extract text content from Notion blocks."""
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
        """Create a Notion text block."""
        return {
            "object": "block",
            "type": block_type,
            block_type: {"rich_text": [{"type": "text", "text": {"content": text}}]},
        }

    async def validate_config(
        self,
        operation: str,
        config: dict[str, Any] | None = None
    ) -> bool:
        """Validate Notion-specific operation configuration."""
        if not await super().validate_config(operation, config):
            return False

        config = config or {}

        # Operation-specific validation
        if operation == "create_page":
            if "parent" not in config:
                return False
            if "properties" not in config:
                return False
                
        elif operation == "update_page":
            if "blocks" not in config:
                return False
                
        elif operation == "query_database":
            # Filter and sorts are optional
            pass

        return True