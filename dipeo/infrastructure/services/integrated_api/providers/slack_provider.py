"""Slack provider for integrated API service."""

import logging
from typing import Any, Optional

from dipeo.infra.adapters.http.api_service import APIService
from dipeo.domain.api.services import APIBusinessLogic
from .base_provider import BaseApiProvider

logger = logging.getLogger(__name__)


class SlackProvider(BaseApiProvider):
    """Slack API provider implementation."""

    SUPPORTED_OPERATIONS = [
        "send_message",
        "read_channel",
        "create_channel",
        "list_channels",
        "upload_file"
    ]

    SLACK_API_BASE = "https://slack.com/api"

    def __init__(self, api_service: APIService | None = None):
        super().__init__("slack", self.SUPPORTED_OPERATIONS)
        self._api_service = api_service

    async def initialize(self) -> None:
        """Initialize the Slack provider."""
        await super().initialize()
        if not self._api_service:
            # Create API service if not injected
            business_logic = APIBusinessLogic()
            self._api_service = APIService(business_logic)

    async def _execute_operation(
        self,
        operation: str,
        config: dict[str, Any],
        resource_id: Optional[str],
        api_key: str,
        timeout: float
    ) -> dict[str, Any]:
        """Execute Slack-specific operations."""
        
        # Common headers for Slack API
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }

        if operation == "send_message":
            channel = resource_id or config.get("channel")
            if not channel:
                raise ValueError("Channel ID required for send_message")
            
            text = config.get("text", "")
            blocks = config.get("blocks")
            
            data = {
                "channel": channel,
                "text": text
            }
            if blocks:
                data["blocks"] = blocks

            result = await self._api_service.execute_with_retry(
                url=f"{self.SLACK_API_BASE}/chat.postMessage",
                method="POST",
                data=data,
                headers=headers,
                timeout=timeout
            )
            
        elif operation == "list_channels":
            params = {
                "types": config.get("types", "public_channel"),
                "limit": config.get("limit", 100)
            }
            
            result = await self._api_service.execute_with_retry(
                url=f"{self.SLACK_API_BASE}/conversations.list",
                method="GET",
                data=params,
                headers=headers,
                timeout=timeout
            )
            
        elif operation == "create_channel":
            name = config.get("name")
            if not name:
                raise ValueError("Channel name required for create_channel")
            
            data = {
                "name": name,
                "is_private": config.get("is_private", False)
            }
            
            result = await self._api_service.execute_with_retry(
                url=f"{self.SLACK_API_BASE}/conversations.create",
                method="POST",
                data=data,
                headers=headers,
                timeout=timeout
            )
            
        elif operation == "read_channel":
            channel = resource_id or config.get("channel")
            if not channel:
                raise ValueError("Channel ID required for read_channel")
            
            params = {
                "channel": channel,
                "limit": config.get("limit", 100)
            }
            
            result = await self._api_service.execute_with_retry(
                url=f"{self.SLACK_API_BASE}/conversations.history",
                method="GET",
                data=params,
                headers=headers,
                timeout=timeout
            )
            
        elif operation == "upload_file":
            # This would require multipart form data handling
            raise NotImplementedError("File upload not yet implemented")
            
        else:
            raise ValueError(f"Unknown operation: {operation}")

        # Check Slack's response format
        if not result.get("ok"):
            error = result.get("error", "Unknown error")
            raise Exception(f"Slack API error: {error}")

        return self._build_success_response(result, operation)

    async def validate_config(
        self,
        operation: str,
        config: dict[str, Any] | None = None
    ) -> bool:
        """Validate Slack-specific operation configuration."""
        if not await super().validate_config(operation, config):
            return False

        config = config or {}

        # Operation-specific validation
        if operation == "send_message":
            if not config.get("text") and not config.get("blocks"):
                return False
                
        elif operation == "create_channel":
            if "name" not in config:
                return False

        return True