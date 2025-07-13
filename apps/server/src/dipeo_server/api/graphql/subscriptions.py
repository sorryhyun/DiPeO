"""GraphQL subscriptions with direct streaming (no EventBus)."""

import asyncio
import logging
from collections.abc import AsyncGenerator
from datetime import datetime

import strawberry
from dipeo.models import ExecutionStatus, NodeExecutionStatus, NodeType

from .context import GraphQLContext
from .types import (
    DiagramID,
    DomainDiagramType,
    ExecutionID,
    ExecutionStateType,
    ExecutionStatusEnum,
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
        state_store = context.get_service("state_store")

        # Subscription started for execution updates

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
                # Execution already completed
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
                        if update.get("type") == "execution_complete":
                            # Give the persistence layer a brief moment to flush the
                            # final state to the database.
                            await asyncio.sleep(0.2)

                        # Try cache first – it's faster.
                        state = await state_store.get_state_from_cache(execution_id)

                        # Fall back to database when the state is no longer in cache
                        # (e.g., after completion when it has been evicted).
                        if not state:
                            state = await state_store.get_state(execution_id)

                        if state:
                            yield state
                        else:
                            break

                    # Check if execution is complete
                    if state and state.status in [
                        ExecutionStatus.COMPLETED,
                        ExecutionStatus.FAILED,
                        ExecutionStatus.ABORTED,
                    ]:
                        # Execution completed
                        break

                except TimeoutError:
                    state = await state_store.get_state_from_cache(execution_id)
                    if not state:
                        state = await state_store.get_state(execution_id)
                    if state:
                        yield state

        except asyncio.CancelledError:
            # Subscription cancelled
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
    ) -> AsyncGenerator[ExecutionStatusEnum]:
        """Streams execution status updates using direct streaming."""
        # Event stream subscription started

        queue = await streaming_manager.subscribe(execution_id)

        try:
            while True:
                try:
                    # Wait for updates
                    update = await asyncio.wait_for(queue.get(), timeout=30.0)

                    # Return execution status from execution_complete events
                    if update.get("type") == "execution_complete":
                        status = update.get("status", "completed")

                        # Map status string to ExecutionStatus enum
                        if status == "completed":
                            yield ExecutionStatusEnum(ExecutionStatus.COMPLETED)
                        elif status == "failed":
                            yield ExecutionStatusEnum(ExecutionStatus.FAILED)
                        elif status == "aborted":
                            yield ExecutionStatusEnum(ExecutionStatus.ABORTED)
                        elif status == "running":
                            yield ExecutionStatusEnum(ExecutionStatus.RUNNING)
                        elif status == "paused":
                            yield ExecutionStatusEnum(ExecutionStatus.PAUSED)
                        else:
                            yield ExecutionStatusEnum(ExecutionStatus.PENDING)

                        # Event stream completed
                        break

                except TimeoutError:
                    # Heartbeat - no action needed
                    pass

        except asyncio.CancelledError:
            # Event subscription cancelled
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
        # Node updates subscription started

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
                            output_value = output_data.get("value")
                            metadata = output_data.get("metadata")
                            if metadata and isinstance(metadata, dict):
                                # Get token usage from tokenUsage object
                                token_usage = metadata.get("tokenUsage", {})
                                if isinstance(token_usage, dict):
                                    tokens_used = token_usage.get("total", 0)
                                else:
                                    tokens_used = 0

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
                        # Node updates completed
                        break

                except TimeoutError:
                    # Heartbeat - no action needed
                    pass

        except asyncio.CancelledError:
            # Node update subscription cancelled
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
        state_store = context.get_service("state_store")

        # Interactive prompts subscription started

        has_yielded = False

        try:
            while True:
                # Use cache for active execution monitoring
                state = await state_store.get_state_from_cache(execution_id)
                if not state:
                    # Fall back to database if not in cache
                    state = await state_store.get_state(execution_id)

                # Check if execution is complete
                if state and state.status in [
                    ExecutionStatus.COMPLETED,
                    ExecutionStatus.FAILED,
                    ExecutionStatus.ABORTED,
                ]:
                    # Interactive prompts completed
                    # Ensure we yield at least once to make this a valid async generator
                    if not has_yielded:
                        yield None
                    break

                # Poll interval (100ms)
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            # Subscription cancelled
            raise
        except Exception as e:
            logger.error(f"Error in interactive prompt stream for {execution_id}: {e}")
            raise


# Function to be called by execution service to publish updates
async def publish_execution_update(execution_id: str, update: dict):
    """Publish an execution update to all subscribers."""
    await streaming_manager.publish(execution_id, update)
