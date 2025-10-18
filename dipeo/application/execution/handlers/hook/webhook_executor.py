import asyncio
from typing import Any

import aiohttp

from dipeo.application.execution.engine.request import ExecutionRequest
from dipeo.diagram_generated.unified_nodes.hook_node import HookNode
from dipeo.domain.base.exceptions import NodeExecutionError
from dipeo.domain.events import DomainEvent


async def execute_webhook_hook(
    node: HookNode, inputs: dict[str, Any], request: ExecutionRequest[HookNode]
) -> Any:
    """Send HTTP request with inputs or subscribe to webhook events."""
    config = node.config

    if config.get("subscribe_to"):
        return await _subscribe_to_webhook_events(node, inputs)

    url = config.get("url")

    method = config.get("method", "POST")
    headers = config.get("headers", {})
    headers["Content-Type"] = "application/json"

    payload = {"inputs": inputs, "hook_type": "hook_node", "node_id": node.label}

    timeout_value = request.get_handler_state("timeout", 30)
    timeout = aiohttp.ClientTimeout(total=timeout_value)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        try:
            async with session.request(
                method=method, url=url, headers=headers, json=payload
            ) as response:
                response.raise_for_status()
                return await response.json()
        except aiohttp.ClientError as e:
            raise NodeExecutionError(f"Webhook request failed: {e!s}") from e


async def _subscribe_to_webhook_events(node: HookNode, inputs: dict[str, Any]) -> Any:
    """Wait for webhook event matching provider and filters, with timeout."""
    config = node.config
    subscribe_config = config.get("subscribe_to", {})

    provider = subscribe_config.get("provider")
    event_name = subscribe_config.get("event_name")
    timeout = subscribe_config.get("timeout", 60)
    filter_conditions = subscribe_config.get("filters", {})

    if not provider:
        raise NodeExecutionError("Webhook subscription requires 'provider' in subscribe_to config")

    received_event = None
    event_received = asyncio.Event()

    class WebhookEventConsumer:
        async def handle(self, event: DomainEvent) -> None:
            nonlocal received_event

            event_data = event.payload
            if event_data.get("source") != "webhook":
                return

            if event_data.get("provider") != provider:
                return

            if event_name and event_data.get("event_name") != event_name:
                return

            payload = event_data.get("payload", {})
            for key, expected_value in filter_conditions.items():
                if payload.get(key) != expected_value:
                    return

            received_event = event_data
            event_received.set()

    try:
        await asyncio.wait_for(event_received.wait(), timeout=timeout)

        if received_event:
            return {
                "status": "triggered",
                "provider": provider,
                "event_name": received_event.get("event_name"),
                "payload": received_event.get("payload"),
                "headers": received_event.get("headers", {}),
            }
        else:
            return {
                "status": "timeout",
                "provider": provider,
                "message": f"No matching webhook event received within {timeout} seconds",
            }

    except TimeoutError:
        return {
            "status": "timeout",
            "provider": provider,
            "message": f"Webhook subscription timed out after {timeout} seconds",
        }
