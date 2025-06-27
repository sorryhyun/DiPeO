"""GraphQL subscriptions with direct streaming (no EventBus)."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from datetime import datetime

import strawberry
from dipeo_domain import EventType, ExecutionStatus, NodeExecutionStatus, NodeType

from .context import GraphQLContext
from .types import (
    DiagramID,
    DomainDiagramType,
    ExecutionEventType,
    ExecutionID,
    ExecutionStateType,
    JSONScalar,
    NodeID,
)

logger = logging.getLogger(__name__)


class StreamingManager:
    """Manages direct streaming connections without EventBus."""

    def __init__(self):
        # Map of execution_id to set of subscriber queues
        self._subscribers: dict[str, set[asyncio.Queue]] = {}
        self._lock = asyncio.Lock()

    async def subscribe(self, execution_id: str) -> asyncio.Queue:
        """Subscribe to execution updates."""
        async with self._lock:
            if execution_id not in self._subscribers:
                self._subscribers[execution_id] = set()

            queue = asyncio.Queue()
            self._subscribers[execution_id].add(queue)
            return queue

    async def unsubscribe(self, execution_id: str, queue: asyncio.Queue):
        """Unsubscribe from execution updates."""
        async with self._lock:
            if execution_id in self._subscribers:
                self._subscribers[execution_id].discard(queue)
                if not self._subscribers[execution_id]:
                    del self._subscribers[execution_id]

    async def publish(self, execution_id: str, update: dict):
        """Publish update to all subscribers."""
        async with self._lock:
            if execution_id in self._subscribers:
                # Create tasks for all queue puts to avoid blocking
                tasks = []
                for queue in self._subscribers[execution_id]:
                    tasks.append(asyncio.create_task(queue.put(update)))

                # Wait for all puts to complete
                if tasks:
                    await asyncio.gather(*tasks, return_exceptions=True)


# Global streaming manager instance
streaming_manager = StreamingManager()


@strawberry.type
class NodeExecution:
    """Node execution state updates."""

    execution_id: ExecutionID
    node_id: NodeID
    node_type: NodeType
    status: str
    progress: str | None = None
    output: JSONScalar | None = None
    error: str | None = None
    tokens_used: int | None = None
    timestamp: datetime


@strawberry.type
class InteractivePrompt:
    """User input prompt during execution."""

    execution_id: ExecutionID
    node_id: NodeID
    prompt: str
    timeout_seconds: int | None = None
    timestamp: datetime


@strawberry.type
class Subscription:
    """GraphQL subscriptions with direct streaming (no EventBus)."""

    @strawberry.subscription
    async def execution_updates(
        self, info: strawberry.Info[GraphQLContext], execution_id: ExecutionID
    ) -> AsyncGenerator[ExecutionStateType]:
        """Streams execution state changes using direct streaming."""
        context: GraphQLContext = info.context
        state_store = context.state_store

        logger.info(
            f"Starting direct execution updates subscription for {execution_id}"
        )

        # Get initial state
        state = await state_store.get_state_from_cache(execution_id)
        if not state:
            state = await state_store.get_state(execution_id)

        if state:
            yield state

            # If already completed, return immediately
            if state.status in [
                ExecutionStatus.COMPLETED,
                ExecutionStatus.FAILED,
                ExecutionStatus.ABORTED,
            ]:
                logger.info(
                    f"Execution {execution_id} already completed with status: {state.status}"
                )
                return

        # Subscribe to direct updates
        queue = await streaming_manager.subscribe(execution_id)

        try:
            while True:
                try:
                    # Wait for updates with timeout for connection health
                    update = await asyncio.wait_for(queue.get(), timeout=30.0)

                    # Process different update types
                    if update.get("type") == "state_update":
                        # Direct state update
                        state = update.get("state")
                        if state:
                            yield state
                    else:
                        # For other updates, fetch current state
                        state = await state_store.get_state_from_cache(execution_id)
                        if state:
                            yield state

                    # Check if execution is complete
                    if state and state.status in [
                        ExecutionStatus.COMPLETED,
                        ExecutionStatus.FAILED,
                        ExecutionStatus.ABORTED,
                    ]:
                        logger.info(
                            f"Execution {execution_id} completed with status: {state.status}"
                        )
                        break

                except TimeoutError:
                    # Send heartbeat by re-fetching state
                    state = await state_store.get_state_from_cache(execution_id)
                    if state:
                        yield state

        except asyncio.CancelledError:
            logger.info(f"Direct subscription cancelled for execution {execution_id}")
            raise
        except Exception as e:
            logger.error(f"Error in direct execution stream for {execution_id}: {e}")
            raise
        finally:
            # Cleanup subscription
            await streaming_manager.unsubscribe(execution_id, queue)

    @strawberry.subscription
    async def execution_events(
        self,
        info: strawberry.Info[GraphQLContext],
        execution_id: ExecutionID,
        event_types: list[EventType] | None = None,
    ) -> AsyncGenerator[ExecutionEventType]:
        """Streams specific execution event types using direct streaming."""
        logger.info(f"Starting direct event stream subscription for {execution_id}")

        sequence = 0
        queue = await streaming_manager.subscribe(execution_id)

        try:
            while True:
                try:
                    # Wait for updates
                    update = await asyncio.wait_for(queue.get(), timeout=30.0)

                    # Map update types to events
                    if update.get("type") == "node_update":
                        data = update.get("data", {})
                        node_id = data.get("node_id")
                        state = data.get("state", "")

                        # Map state to event type
                        if state == NodeExecutionStatus.RUNNING.value:
                            event_type = EventType.NODE_STARTED
                        elif state == NodeExecutionStatus.COMPLETED.value:
                            event_type = EventType.NODE_COMPLETED
                        elif state == NodeExecutionStatus.FAILED.value:
                            event_type = EventType.NODE_FAILED
                        elif state == NodeExecutionStatus.SKIPPED.value:
                            event_type = EventType.NODE_SKIPPED
                        else:
                            continue

                        if not event_types or event_type in event_types:
                            sequence += 1

                            event_data = {
                                "status": state,
                            }

                            if state == NodeExecutionStatus.FAILED.value:
                                event_data["error"] = data.get("error")
                            elif state == NodeExecutionStatus.COMPLETED.value:
                                output = data.get("output", {})
                                if isinstance(output, dict):
                                    event_data["output"] = output.get("data")

                            yield ExecutionEventType(
                                execution_id=execution_id,
                                sequence=sequence,
                                event_type=event_type,
                                node_id=NodeID(node_id) if node_id else None,
                                timestamp=data.get(
                                    "timestamp", datetime.utcnow().isoformat()
                                ),
                                data=event_data,
                            )

                    elif update.get("type") == "execution_complete":
                        sequence += 1
                        status = update.get("status", "completed")

                        if status == "completed":
                            event_type = EventType.EXECUTION_COMPLETED
                        elif status == "failed":
                            event_type = EventType.EXECUTION_FAILED
                        elif status == "aborted":
                            event_type = EventType.EXECUTION_ABORTED
                        else:
                            event_type = EventType.EXECUTION_UPDATE

                        if not event_types or event_type in event_types:
                            yield ExecutionEventType(
                                execution_id=execution_id,
                                sequence=sequence,
                                event_type=event_type,
                                node_id=None,
                                timestamp=datetime.utcnow().isoformat(),
                                data={
                                    "status": status,
                                    "error": update.get("error"),
                                },
                            )

                        logger.info(
                            f"Direct event stream completed for execution {execution_id}"
                        )
                        break

                except TimeoutError:
                    # Heartbeat - no action needed
                    pass

        except asyncio.CancelledError:
            logger.info(
                f"Direct event subscription cancelled for execution {execution_id}"
            )
            raise
        except Exception as e:
            logger.error(f"Error in direct event stream for {execution_id}: {e}")
            raise
        finally:
            # Cleanup subscription
            await streaming_manager.unsubscribe(execution_id, queue)

    @strawberry.subscription
    async def node_updates(
        self,
        info: strawberry.Info[GraphQLContext],
        execution_id: ExecutionID,
        node_types: list[NodeType] | None = None,
    ) -> AsyncGenerator[NodeExecution]:
        """Streams node execution updates with direct streaming."""
        logger.info(f"Starting direct node updates subscription for {execution_id}")

        # Subscribe to direct updates
        queue = await streaming_manager.subscribe(execution_id)

        try:
            while True:
                try:
                    # Wait for updates
                    update = await asyncio.wait_for(queue.get(), timeout=30.0)

                    # Process node update events
                    if update.get("type") == "node_update":
                        data = update.get("data", {})
                        node_id = data.get("node_id")
                        if not node_id:
                            continue

                        # Extract node type
                        node_type = NodeType(data.get("node_type", "job"))

                        if node_types and node_type not in node_types:
                            continue

                        # Map state to status string
                        state = data.get("state", "")
                        status_map = {
                            NodeExecutionStatus.PENDING.value: "pending",
                            NodeExecutionStatus.RUNNING.value: "running",
                            NodeExecutionStatus.COMPLETED.value: "completed",
                            NodeExecutionStatus.FAILED.value: "failed",
                            NodeExecutionStatus.SKIPPED.value: "skipped",
                            NodeExecutionStatus.PAUSED.value: "paused",
                        }
                        status = status_map.get(state, state)

                        # Extract output and tokens
                        output_data = data.get("output")
                        output_value = None
                        tokens_used = None

                        if output_data and isinstance(output_data, dict):
                            output_value = output_data.get("data")
                            metadata = output_data.get("metadata", {})
                            usage = metadata.get("usage", {})
                            if usage:
                                tokens_used = usage.get("total_tokens", 0)

                        yield NodeExecution(
                            execution_id=execution_id,
                            node_id=NodeID(node_id),
                            node_type=node_type,
                            status=status,
                            progress=None,
                            output=output_value,
                            error=data.get("error"),
                            tokens_used=tokens_used,
                            timestamp=datetime.fromisoformat(
                                data.get("timestamp", datetime.utcnow().isoformat())
                            ),
                        )

                    elif update.get("type") == "execution_complete":
                        logger.info(
                            f"Node updates completed for execution {execution_id}"
                        )
                        break

                except TimeoutError:
                    # Heartbeat - no action needed
                    pass

        except asyncio.CancelledError:
            logger.info(
                f"Direct node update subscription cancelled for execution {execution_id}"
            )
            raise
        except Exception as e:
            logger.error(f"Error in direct node update stream for {execution_id}: {e}")
            raise
        finally:
            # Cleanup subscription
            await streaming_manager.unsubscribe(execution_id, queue)

    @strawberry.subscription
    async def diagram_changes(
        self, info: strawberry.Info[GraphQLContext], diagram_id: DiagramID
    ) -> AsyncGenerator[DomainDiagramType]:
        """Streams diagram modifications (not implemented)."""
        logger.warning(f"Diagram change stream not yet implemented for {diagram_id}")
        while False:
            yield

    @strawberry.subscription
    async def interactive_prompts(
        self, info: strawberry.Info[GraphQLContext], execution_id: ExecutionID
    ) -> AsyncGenerator[InteractivePrompt | None]:
        """Streams interactive prompts requiring user response."""
        context: GraphQLContext = info.context
        state_store = context.state_store

        logger.info(f"Starting interactive prompts subscription for {execution_id}")

        has_yielded = False

        try:
            while True:
                # Use cache for active execution monitoring
                state = await state_store.get_state_from_cache(execution_id)
                if not state:
                    # Fall back to database if not in cache
                    state = await state_store.get_state(execution_id)

                # TODO: Check for actual interactive prompts in the state
                # For now, this is a placeholder implementation

                # Check if execution is complete
                if state and state.status in [
                    ExecutionStatus.COMPLETED,
                    ExecutionStatus.FAILED,
                    ExecutionStatus.ABORTED,
                ]:
                    logger.info(
                        f"Interactive prompts completed for execution {execution_id}"
                    )
                    # Ensure we yield at least once to make this a valid async generator
                    if not has_yielded:
                        yield None
                    break

                # Poll interval (100ms)
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info(
                f"Interactive prompt subscription cancelled for execution {execution_id}"
            )
            raise
        except Exception as e:
            logger.error(f"Error in interactive prompt stream for {execution_id}: {e}")
            raise


# Rename the old subscription class for backward compatibility
DirectStreamingSubscription = Subscription


# Function to be called by execution service to publish updates
async def publish_execution_update(execution_id: str, update: dict):
    """Publish an execution update to all subscribers."""
    await streaming_manager.publish(execution_id, update)
