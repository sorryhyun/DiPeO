"""GraphQL subscriptions for real-time execution updates."""

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, List, Optional

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


@strawberry.type
class NodeExecution:
    """Node execution state updates."""

    execution_id: ExecutionID
    node_id: NodeID
    node_type: NodeType
    status: str
    progress: Optional[str] = None
    output: Optional[JSONScalar] = None
    error: Optional[str] = None
    tokens_used: Optional[int] = None
    timestamp: datetime


@strawberry.type
class InteractivePrompt:
    """User input prompt during execution."""

    execution_id: ExecutionID
    node_id: NodeID
    prompt: str
    timeout_seconds: Optional[int] = None
    timestamp: datetime


@strawberry.type
class Subscription:
    """GraphQL subscriptions for DiPeO real-time updates."""

    @strawberry.subscription
    async def execution_updates(
        self, info: strawberry.Info[GraphQLContext], execution_id: ExecutionID
    ) -> AsyncGenerator[ExecutionStateType, None]:
        """Streams execution state changes using push-based updates."""
        context: GraphQLContext = info.context
        state_store = context.state_store
        event_bus = context.event_bus

        logger.info(f"Starting execution updates subscription for {execution_id}")

        # First, yield the current state if it exists
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

        # Subscribe to real-time updates via EventBus
        updates_queue = asyncio.Queue()
        
        async def handle_update(event: dict) -> None:
            await updates_queue.put(event)
        
        channel = f"execution:{execution_id}"
        subscription_id = await event_bus.subscribe(channel, handle_update)
        
        try:
            while True:
                try:
                    # Wait for updates with a timeout for connection health
                    update = await asyncio.wait_for(updates_queue.get(), timeout=30.0)
                    
                    # Fetch the latest state after receiving an update
                    state = await state_store.get_state(execution_id)
                    if state:
                        yield state
                        
                        # Check if execution is complete
                        if state.status in [
                            ExecutionStatus.COMPLETED,
                            ExecutionStatus.FAILED,
                            ExecutionStatus.ABORTED,
                        ]:
                            logger.info(
                                f"Execution {execution_id} completed with status: {state.status}"
                            )
                            break
                            
                except asyncio.TimeoutError:
                    # Send periodic heartbeat by re-fetching state
                    state = await state_store.get_state(execution_id)
                    if state:
                        yield state
                        
        except asyncio.CancelledError:
            logger.info(f"Subscription cancelled for execution {execution_id}")
            raise
        except Exception as e:
            logger.error(f"Error in execution stream for {execution_id}: {e}")
            raise
        finally:
            # Cleanup subscription
            await event_bus.unsubscribe(subscription_id)

    @strawberry.subscription
    async def execution_events(
        self,
        info: strawberry.Info[GraphQLContext],
        execution_id: ExecutionID,
        event_types: Optional[List[EventType]] = None,
    ) -> AsyncGenerator[ExecutionEventType, None]:
        """Streams specific execution event types using push-based updates."""
        context: GraphQLContext = info.context
        state_store = context.state_store
        event_bus = context.event_bus

        logger.info(f"Starting event stream subscription for {execution_id}")

        sequence = 0
        last_node_states = {}
        
        # Process initial state
        state = await state_store.get_state(execution_id)
        if state:
            current_node_states = state.node_states or {}
            last_node_states = {
                nid: ns for nid, ns in current_node_states.items()
            }

        # Subscribe to real-time updates
        updates_queue = asyncio.Queue()
        
        async def handle_update(event: dict) -> None:
            await updates_queue.put(event)
        
        channel = f"execution:{execution_id}"
        subscription_id = await event_bus.subscribe(channel, handle_update)

        try:
            while True:
                try:
                    # Wait for updates
                    update = await asyncio.wait_for(updates_queue.get(), timeout=30.0)
                    
                    # Process update based on type
                    if update.get("type") == "node_start":
                        sequence += 1
                        event_type = EventType.NODE_STARTED
                        
                        if not event_types or event_type in event_types:
                            yield ExecutionEventType(
                                execution_id=execution_id,
                                sequence=sequence,
                                event_type=event_type,
                                node_id=NodeID(update["node_id"]),
                                timestamp=datetime.now().isoformat(),
                                data={"status": "running"},
                            )
                    
                    elif update.get("type") == "node_complete":
                        sequence += 1
                        status = update.get("status", "completed")
                        event_type = {
                            "completed": EventType.NODE_COMPLETED,
                            "failed": EventType.NODE_FAILED,
                            "skipped": EventType.NODE_SKIPPED,
                        }.get(status, EventType.NODE_COMPLETED)
                        
                        if not event_types or event_type in event_types:
                            output_data = update.get("output", {})
                            yield ExecutionEventType(
                                execution_id=execution_id,
                                sequence=sequence,
                                event_type=event_type,
                                node_id=NodeID(update["node_id"]),
                                timestamp=datetime.now().isoformat(),
                                data={
                                    "status": status,
                                    "output": output_data.get("value") if isinstance(output_data, dict) else None,
                                    "error": update.get("error"),
                                },
                            )
                    
                    elif update.get("type") == "execution_complete":
                        sequence += 1
                        status = update.get("status", "completed")
                        final_event_type = {
                            "completed": EventType.EXECUTION_COMPLETED,
                            "failed": EventType.EXECUTION_FAILED,
                            "aborted": EventType.EXECUTION_ABORTED,
                        }.get(status, EventType.EXECUTION_UPDATE)
                        
                        if not event_types or final_event_type in event_types:
                            yield ExecutionEventType(
                                execution_id=execution_id,
                                sequence=sequence,
                                event_type=final_event_type,
                                node_id=None,
                                timestamp=datetime.now().isoformat(),
                                data={
                                    "status": status,
                                    "error": update.get("error"),
                                },
                            )
                        
                        logger.info(
                            f"Event stream completed for execution {execution_id}"
                        )
                        break
                        
                except asyncio.TimeoutError:
                    # Heartbeat - no action needed
                    pass

        except asyncio.CancelledError:
            logger.info(f"Event subscription cancelled for execution {execution_id}")
            raise
        except Exception as e:
            logger.error(f"Error in event stream for {execution_id}: {e}")
            raise
        finally:
            # Cleanup subscription
            await event_bus.unsubscribe(subscription_id)

    @strawberry.subscription
    async def node_updates(
        self,
        info: strawberry.Info[GraphQLContext],
        execution_id: ExecutionID,
        node_types: Optional[List[NodeType]] = None,
    ) -> AsyncGenerator[NodeExecution, None]:
        """Streams node execution updates with optional filtering using push-based updates."""
        context: GraphQLContext = info.context
        state_store = context.state_store
        event_bus = context.event_bus

        logger.info(f"Starting node updates subscription for {execution_id}")

        # Subscribe to real-time updates
        updates_queue = asyncio.Queue()
        
        async def handle_update(event: dict) -> None:
            await updates_queue.put(event)
        
        channel = f"execution:{execution_id}"
        subscription_id = await event_bus.subscribe(channel, handle_update)

        try:
            while True:
                try:
                    # Wait for updates
                    update = await asyncio.wait_for(updates_queue.get(), timeout=30.0)
                    
                    # Process node updates
                    if update.get("type") in ["node_start", "node_complete"]:
                        node_id = update.get("node_id")
                        if not node_id:
                            continue
                            
                        # Get node type from update or default to job
                        node_type = NodeType(update.get("node_type", "job"))
                        
                        if node_types and node_type not in node_types:
                            continue
                        
                        # Extract status from update
                        if update.get("type") == "node_start":
                            status = NodeExecutionStatus.RUNNING
                        else:
                            status_str = update.get("status", "completed")
                            status = {
                                "completed": NodeExecutionStatus.COMPLETED,
                                "failed": NodeExecutionStatus.FAILED,
                                "skipped": NodeExecutionStatus.SKIPPED,
                            }.get(status_str, NodeExecutionStatus.COMPLETED)
                        
                        # Extract output and metadata
                        output_data = update.get("output", {})
                        output_value = None
                        tokens_used = None
                        
                        if isinstance(output_data, dict):
                            output_value = output_data.get("value")
                            metadata = output_data.get("metadata", {})
                            if "tokens_used" in metadata:
                                tokens_used = metadata["tokens_used"]
                        
                        yield NodeExecution(
                            execution_id=execution_id,
                            node_id=NodeID(node_id),
                            node_type=node_type,
                            status=status,
                            progress=None,
                            output=output_value,
                            error=update.get("error"),
                            tokens_used=tokens_used,
                            timestamp=datetime.now(),
                        )
                    
                    elif update.get("type") == "execution_complete":
                        logger.info(
                            f"Node updates completed for execution {execution_id}"
                        )
                        break
                        
                except asyncio.TimeoutError:
                    # Heartbeat - no action needed
                    pass

        except asyncio.CancelledError:
            logger.info(
                f"Node update subscription cancelled for execution {execution_id}"
            )
            raise
        except Exception as e:
            logger.error(f"Error in node update stream for {execution_id}: {e}")
            raise
        finally:
            # Cleanup subscription
            await event_bus.unsubscribe(subscription_id)

    @strawberry.subscription
    async def diagram_changes(
        self, info: strawberry.Info[GraphQLContext], diagram_id: DiagramID
    ) -> AsyncGenerator[DomainDiagramType, None]:
        """Streams diagram modifications (not implemented)."""
        logger.warning(f"Diagram change stream not yet implemented for {diagram_id}")
        while False:
            yield

    @strawberry.subscription
    async def interactive_prompts(
        self, info: strawberry.Info[GraphQLContext], execution_id: ExecutionID
    ) -> AsyncGenerator[Optional[InteractivePrompt], None]:
        """Streams interactive prompts requiring user response."""
        context: GraphQLContext = info.context
        state_store = context.state_store

        logger.info(f"Starting interactive prompts subscription for {execution_id}")

        processed_prompts = set()
        has_yielded = False

        try:
            while True:
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


def _map_status(status: str) -> ExecutionStatus:
    """Maps status string to ExecutionStatus enum."""
    status_map = {
        "started": ExecutionStatus.STARTED,
        "running": ExecutionStatus.RUNNING,
        "paused": ExecutionStatus.PAUSED,
        "completed": ExecutionStatus.COMPLETED,
        "failed": ExecutionStatus.FAILED,
        "cancelled": ExecutionStatus.ABORTED,
        "aborted": ExecutionStatus.ABORTED,
    }
    return status_map.get(status.lower(), ExecutionStatus.STARTED)


def _get_event_type_for_status(status: str) -> EventType:
    """Maps node status to event type."""
    status_event_map = {
        "started": EventType.NODE_STARTED,
        "running": EventType.NODE_RUNNING,
        "completed": EventType.NODE_COMPLETED,
        "failed": EventType.NODE_FAILED,
        "skipped": EventType.NODE_SKIPPED,
        "paused": EventType.NODE_PAUSED,
    }
    return status_event_map.get(status, EventType.EXECUTION_UPDATE)


def _get_event_type_for_node_status(status: NodeExecutionStatus) -> EventType:
    """Maps NodeExecutionStatus to EventType."""
    status_event_map = {
        NodeExecutionStatus.PENDING: EventType.NODE_STARTED,
        NodeExecutionStatus.RUNNING: EventType.NODE_RUNNING,
        NodeExecutionStatus.COMPLETED: EventType.NODE_COMPLETED,
        NodeExecutionStatus.FAILED: EventType.NODE_FAILED,
        NodeExecutionStatus.SKIPPED: EventType.NODE_SKIPPED,
        NodeExecutionStatus.PAUSED: EventType.NODE_PAUSED,
    }
    return status_event_map.get(status, EventType.EXECUTION_UPDATE)


def _get_node_type(diagram: dict, node_id: str) -> NodeType:
    """Extracts node type from diagram data."""
    if not diagram or "nodes" not in diagram:
        return NodeType.job

    node = diagram["nodes"].get(node_id, {})
    node_type_str = node.get("type", "job")

    try:
        return NodeType(node_type_str)
    except ValueError:
        return NodeType.job
