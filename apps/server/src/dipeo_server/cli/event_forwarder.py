"""Event forwarder that sends CLI execution events to the background server."""

import asyncio
import contextlib
from typing import Any

import httpx

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.graphql.inputs import UpdateNodeStateInput
from dipeo.diagram_generated.graphql.operations import UpdateNodeStateOperation
from dipeo.domain.events import DomainEvent, EventType

logger = get_module_logger(__name__)


class EventForwarder:
    """Forwards execution events from CLI to background server via GraphQL."""

    def __init__(self, execution_id: str, server_url: str = "http://localhost:8000"):
        self.execution_id = execution_id
        self.server_url = server_url
        self.graphql_endpoint = f"{server_url}/graphql"
        self._running = False
        self._event_queue: asyncio.Queue[DomainEvent] = asyncio.Queue()
        self._forward_task: asyncio.Task | None = None

    async def start(self) -> None:
        """Start the event forwarder."""
        self._running = True
        self._forward_task = asyncio.create_task(self._process_event_queue())
        logger.debug(f"EventForwarder started for execution {self.execution_id}")

    async def stop(self) -> None:
        """Stop the event forwarder and wait for pending events."""
        self._running = False
        if self._forward_task:
            # Wait for all pending events to be processed
            await self._event_queue.join()
            self._forward_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await self._forward_task
        logger.debug(f"EventForwarder stopped for execution {self.execution_id}")

    async def handle(self, event: DomainEvent) -> None:
        """Handle an event from the event bus (callback for EventBus subscription)."""
        if not self._running:
            return

        # Only forward relevant events for this execution
        if event.scope.execution_id != self.execution_id:
            return

        # Forward node-level AND execution-level events
        if event.type in [
            EventType.NODE_STARTED,
            EventType.NODE_COMPLETED,
            EventType.NODE_ERROR,
            EventType.EXECUTION_COMPLETED,
            EventType.EXECUTION_ERROR,
        ]:
            await self._event_queue.put(event)

    async def _process_event_queue(self) -> None:
        """Process events from the queue and forward to server."""
        while self._running or not self._event_queue.empty():
            try:
                event = await asyncio.wait_for(self._event_queue.get(), timeout=0.1)
                await self._forward_event(event)
                self._event_queue.task_done()
            except TimeoutError:
                continue
            except Exception as e:
                logger.error(f"Error processing event queue: {e}")

    async def _forward_event(self, event: DomainEvent) -> None:
        """Forward a single event to the background server via GraphQL."""
        try:
            # Handle execution-level events differently
            if event.type in [EventType.EXECUTION_COMPLETED, EventType.EXECUTION_ERROR]:
                await self._forward_execution_event(event)
                return

            # Handle node-level events
            # Extract node_id from scope (not payload!)
            node_id = event.scope.node_id
            if not node_id:
                logger.warning(f"Event {event.type} missing node_id in scope, skipping forward")
                return

            # Map event type to status
            status_map = {
                EventType.NODE_STARTED: "RUNNING",
                EventType.NODE_COMPLETED: "COMPLETED",
                EventType.NODE_ERROR: "FAILED",
            }
            status = status_map.get(event.type)
            if not status:
                logger.warning(f"Unknown event type {event.type}, skipping forward")
                return

            # Extract output and error from Pydantic payload
            output = getattr(event.payload, "output", None) if event.payload else None
            error = getattr(event.payload, "error_message", None) if event.payload else None

            # Serialize output if it's a complex object
            if output is not None:
                if hasattr(output, "model_dump"):
                    # Pydantic model
                    output = output.model_dump()
                elif hasattr(output, "to_dict"):
                    # Custom object with to_dict method
                    output = output.to_dict()
                elif not isinstance(output, str | int | float | bool | dict | list | type(None)):
                    # Other complex objects - convert to string
                    output = str(output)

            # Build mutation input (skip output for now - it's not used by update_node_status)
            input_data = UpdateNodeStateInput(
                execution_id=self.execution_id,
                node_id=node_id,
                status=status,
                output=None,  # Skip output - it causes serialization issues and isn't used
                error=error,
            )

            variables = UpdateNodeStateOperation.get_variables_dict(input=input_data)
            query = UpdateNodeStateOperation.get_query()

            # Forward to server with retry logic
            max_retries = 3
            retry_delay = 0.1

            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(timeout=2.0) as client:
                        logger.debug(
                            f"Sending mutation to {self.graphql_endpoint}: status={status}, node={node_id}, exec={self.execution_id}"
                        )
                        response = await client.post(
                            self.graphql_endpoint,
                            json={"query": query, "variables": variables},
                        )
                        result = response.json()
                        logger.debug(f"Response status: {response.status_code}, result: {result}")

                        if response.status_code == 200:
                            if result.get("errors"):
                                logger.error(
                                    f"GraphQL errors forwarding event {event.type} for node {node_id}: {result['errors']}"
                                )
                            else:
                                logger.debug(
                                    f"Forwarded {event.type} for node {node_id} to server (SUCCESS)"
                                )
                            return
                        else:
                            logger.warning(
                                f"Server returned {response.status_code} when forwarding event {event.type} for node {node_id}"
                            )

                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    if attempt < max_retries - 1:
                        logger.debug(
                            f"Failed to forward event (attempt {attempt + 1}/{max_retries}), retrying..."
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 1.0)
                    else:
                        logger.warning(f"Could not forward event after {max_retries} attempts: {e}")
                        return

        except Exception as e:
            logger.error(f"Error forwarding event {event.type}: {e}")

    async def _forward_execution_event(self, event: DomainEvent) -> None:
        """Forward execution-level events (COMPLETED/ERROR) to server via ControlExecution mutation."""
        try:
            # Determine action and error from event type
            if event.type == EventType.EXECUTION_COMPLETED:
                action = "complete"
                reason = "Execution completed successfully"
                error = None
            else:  # EXECUTION_ERROR
                action = "abort"
                error = None
                if event.payload:
                    error = getattr(event.payload, "error_message", None) or getattr(
                        event.payload, "error", None
                    )
                reason = error or "Execution failed"

            logger.debug(
                f"Forwarding execution {event.type}: exec={self.execution_id}, action={action}"
            )

            # Use ControlExecution mutation for both COMPLETED and FAILED
            mutation_query = """
                mutation ControlExecution($input: ExecutionControlInput!) {
                    controlExecution(input: $input) {
                        success
                        message
                        execution {
                            id
                            status
                        }
                    }
                }
            """

            variables = {
                "input": {"execution_id": self.execution_id, "action": action, "reason": reason}
            }

            # Send the mutation with retry logic
            max_retries = 3
            retry_delay = 0.1

            for attempt in range(max_retries):
                try:
                    async with httpx.AsyncClient(timeout=2.0) as client:
                        logger.debug(f"Sending execution {action} to {self.graphql_endpoint}")
                        response = await client.post(
                            self.graphql_endpoint,
                            json={"query": mutation_query, "variables": variables},
                        )
                        result = response.json()

                        if response.status_code == 200:
                            if result.get("errors"):
                                logger.error(
                                    f"GraphQL errors forwarding execution {action}: {result['errors']}"
                                )
                            else:
                                logger.debug(f"Forwarded execution {action} to server (SUCCESS)")
                            return
                        else:
                            logger.warning(
                                f"Server returned {response.status_code} when forwarding execution {action}"
                            )

                except (httpx.ConnectError, httpx.TimeoutException) as e:
                    if attempt < max_retries - 1:
                        logger.debug(
                            f"Failed to forward execution event (attempt {attempt + 1}/{max_retries}), retrying..."
                        )
                        await asyncio.sleep(retry_delay)
                        retry_delay = min(retry_delay * 2, 1.0)
                    else:
                        logger.warning(
                            f"Could not forward execution event after {max_retries} attempts: {e}"
                        )
                        return

        except Exception as e:
            logger.error(f"Error forwarding execution event {event.type}: {e}")
