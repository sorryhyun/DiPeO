"""GraphQL subscription client for real-time updates."""

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)

# Try to import WebSocket dependencies
try:
    from gql import Client, gql
    from gql.transport.websockets import WebsocketsTransport

    HAS_WEBSOCKET_SUPPORT = True
except ImportError:
    HAS_WEBSOCKET_SUPPORT = False
    logger.debug("WebSocket support not available, will use polling")


class SubscriptionClient:
    """Client for GraphQL subscriptions."""

    def __init__(self, url: str, execution_id: str):
        if not HAS_WEBSOCKET_SUPPORT:
            raise ImportError(
                "WebSocket support not available. Install with: uv pip install 'gql[websockets]'"
            )

        self.execution_id = execution_id

        # Convert HTTP URL to WebSocket URL
        ws_url = url.replace("http://", "ws://").replace("https://", "wss://")
        if not ws_url.endswith("/graphql"):
            ws_url = f"{ws_url}/graphql"

        self.ws_url = ws_url
        self.client = None
        self.session = None
        self._subscription = None
        self._stop_event = asyncio.Event()

    async def connect(self):
        """Connect to the GraphQL WebSocket endpoint."""
        try:
            # Create WebSocket transport
            transport = WebsocketsTransport(url=self.ws_url)

            # Create GraphQL client
            self.client = Client(transport=transport, fetch_schema_from_transport=False)
            self.session = await self.client.connect_async(reconnecting=True)

            logger.info(f"Connected to WebSocket: {self.ws_url}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to WebSocket: {e}")
            return False

    async def disconnect(self):
        """Disconnect from the WebSocket."""
        self._stop_event.set()
        if self.session:
            await self.client.close_async()
            self.session = None
        logger.info("Disconnected from WebSocket")

    async def subscribe_to_execution(self, callback: Callable[[dict[str, Any]], None]):
        """Subscribe to execution updates and call callback for each event."""
        if not self.session:
            logger.error("Not connected to WebSocket")
            return

        # Import and use generated subscription
        from dipeo.diagram_generated.graphql.operations import EXECUTION_UPDATES_SUBSCRIPTION

        # GraphQL subscription query
        subscription = gql(EXECUTION_UPDATES_SUBSCRIPTION)

        try:
            # Execute subscription
            async for result in self.session.subscribe(
                subscription, variable_values={"execution_id": self.execution_id}
            ):
                if self._stop_event.is_set():
                    break

                # Extract update data
                update = result.get("execution_updates")
                if update:
                    # Convert the update to event format expected by display
                    event = {
                        "execution_id": update.get("execution_id"),
                        "event_type": update.get("event_type"),
                        "data": update.get("data", {}),
                        "timestamp": update.get("timestamp"),
                    }

                    # Call the callback
                    await asyncio.get_event_loop().run_in_executor(None, callback, event)

        except asyncio.CancelledError:
            logger.info("Subscription cancelled")
        except Exception as e:
            logger.error(f"Subscription error: {e}")
            raise


class SimpleSubscriptionClient:
    """Simplified subscription client using HTTP polling as fallback."""

    def __init__(self, server_manager, execution_id: str):
        self.server_manager = server_manager
        self.execution_id = execution_id
        self._stop_event = asyncio.Event()
        self.last_node_states = {}
        self.last_status = None

    async def connect(self):
        """No-op for polling client."""
        return True

    async def disconnect(self):
        """Stop polling."""
        self._stop_event.set()

    async def subscribe_to_execution(self, callback: Callable[[dict[str, Any]], None]):
        """Poll for execution updates with state tracking."""
        while not self._stop_event.is_set():
            try:
                # Get execution state
                result = self.server_manager.get_execution_result(self.execution_id)

                if result:
                    # Check for status changes
                    status = result.get("status")
                    if status and status != self.last_status:
                        self.last_status = status
                        event = {
                            "execution_id": self.execution_id,
                            "event_type": "EXECUTION_STATUS_CHANGED",
                            "data": {"status": status},
                            "timestamp": None,
                        }
                        await asyncio.get_event_loop().run_in_executor(None, callback, event)

                    # Check for node state changes
                    node_states = result.get("node_states", {})
                    for node_id, state in node_states.items():
                        if isinstance(state, dict):
                            node_status = state.get("status")
                            prev_status = self.last_node_states.get(node_id, {}).get("status")

                            # Emit event if status changed
                            if node_status != prev_status:
                                # Determine event type based on new status
                                if node_status == "RUNNING":
                                    event_type = "NODE_STARTED"
                                elif node_status == "COMPLETED":
                                    event_type = "NODE_COMPLETED"
                                elif node_status == "FAILED":
                                    event_type = "NODE_FAILED"
                                elif node_status == "SKIPPED":
                                    event_type = "NODE_STATUS_CHANGED"
                                else:
                                    event_type = "NODE_STATUS_CHANGED"

                                event = {
                                    "execution_id": self.execution_id,
                                    "event_type": event_type,
                                    "data": {
                                        "node_id": node_id,
                                        "node_type": state.get("node_type", "UNKNOWN"),
                                        "name": state.get("name", node_id),
                                        "status": node_status,
                                        "error": state.get("error")
                                        if node_status == "FAILED"
                                        else None,
                                    },
                                    "timestamp": None,
                                }
                                await asyncio.get_event_loop().run_in_executor(
                                    None, callback, event
                                )

                                # Update tracked state
                                self.last_node_states[node_id] = state

                    # Emit token usage updates if available
                    if "token_usage" in result:
                        event = {
                            "execution_id": self.execution_id,
                            "event_type": "METRICS_COLLECTED",
                            "data": {"token_usage": result["token_usage"]},
                            "timestamp": None,
                        }
                        await asyncio.get_event_loop().run_in_executor(None, callback, event)

                    # Check if execution is done
                    if status in ["COMPLETED", "FAILED", "ABORTED", "MAXITER_REACHED"]:
                        break

            except Exception as e:
                logger.debug(f"Polling error: {e}")

            # Wait before next poll (shorter interval for more responsive updates)
            await asyncio.sleep(0.5)
