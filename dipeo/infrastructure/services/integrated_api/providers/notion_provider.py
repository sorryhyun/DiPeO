"""Notion provider for integrated API service."""

import logging
from typing import Any, Optional

from dipeo.infra.adapters.notion.service import NotionAPIService
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
        self._notion_service = NotionAPIService()

    async def initialize(self) -> None:
        """Initialize the Notion provider."""
        await super().initialize()
        await self._notion_service.initialize()

    async def _execute_operation(
        self,
        operation: str,
        config: dict[str, Any],
        resource_id: Optional[str],
        api_key: str,
        timeout: float
    ) -> dict[str, Any]:
        """Execute Notion-specific operations."""
        
        # Map operations to Notion service methods
        if operation == "read_page":
            if not resource_id:
                raise ValueError("page_id required for read_page operation")
            result = await self._notion_service.retrieve_page(resource_id, api_key)
            
        elif operation == "create_page":
            parent = config.get("parent", {})
            properties = config.get("properties", {})
            children = config.get("children")
            result = await self._notion_service.create_page(
                parent=parent,
                properties=properties,
                children=children,
                api_key=api_key
            )
            
        elif operation == "update_page":
            if not resource_id:
                raise ValueError("page_id required for update_page operation")
            blocks = config.get("blocks", [])
            if blocks:
                result = await self._notion_service.append_blocks(resource_id, blocks, api_key)
            else:
                raise ValueError("update_page requires blocks to append")
                
        elif operation == "query_database":
            if not resource_id:
                raise ValueError("database_id required for query_database operation")
            filter_query = config.get("filter")
            sorts = config.get("sorts")
            result = await self._notion_service.query_database(
                database_id=resource_id,
                filter=filter_query,
                sorts=sorts,
                api_key=api_key
            )
            
        elif operation in ["delete_page", "create_database", "update_database"]:
            # These operations would need to be implemented in NotionAPIService
            raise NotImplementedError(f"Operation '{operation}' not yet implemented")
            
        else:
            raise ValueError(f"Unknown operation: {operation}")

        return self._build_success_response(result, operation)

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