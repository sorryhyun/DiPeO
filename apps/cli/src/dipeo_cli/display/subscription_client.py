"""GraphQL subscription client for real-time updates."""

import asyncio
import json
import logging
from collections.abc import Callable
from typing import Any

from gql import Client, gql
from gql.transport.websockets import WebsocketsTransport

logger = logging.getLogger(__name__)


class SubscriptionClient:
    """Client for GraphQL subscriptions."""

    def __init__(self, url: str, execution_id: str):
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
        """Disconnect from the WebSocket and shut down transport cleanly."""
        self._stop_event.set()
        try:
            if self.session:
                # Close GQL client (awaits WS shutdown)
                await self.client.close_async()
        except Exception as e:
            logger.debug(f"Client close error: {e}")
        finally:
            # Belt-and-suspenders: also close the underlying transport
            try:
                transport = getattr(self.client, "transport", None)
                if transport:
                    close = getattr(transport, "close", None)
                    if callable(close):
                        res = close()
                        if asyncio.iscoroutine(res):
                            await res
            except Exception as e:
                logger.debug(f"Transport close error: {e}")
            self.session = None
            logger.info("Disconnected from WebSocket")

    async def subscribe_to_execution(self, callback: Callable[[dict[str, Any]], None]):
        """Subscribe to execution updates and call callback for each event."""
        if not self.session:
            logger.error("Not connected to WebSocket")
            return

        # Import and use generated subscription
        from dipeo.diagram_generated.graphql.operations import (
            EXECUTION_UPDATES_SUBSCRIPTION,
        )

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
