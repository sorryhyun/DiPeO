"""GraphQL subscriptions for real-time execution updates."""

import asyncio
import logging
from datetime import datetime
from typing import AsyncGenerator, List, Optional

import strawberry
from dipeo_domain import EventType, NodeExecutionStatus

from dipeo_server.core import ExecutionStatus, NodeType

from .context import GraphQLContext
from api.types.domain_types import DomainDiagramType, ExecutionEvent, ExecutionState
from api.types.scalars_types import DiagramID, ExecutionID, JSONScalar, NodeID

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
    ) -> AsyncGenerator[ExecutionState, None]:
        """Streams execution state changes."""
        context: GraphQLContext = info.context
        state_store = context.state_store

        logger.info(f"Starting execution updates subscription for {execution_id}")

        last_update = 0

        try:
            while True:
                # Get latest state
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

                # Poll interval (100ms)
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info(f"Subscription cancelled for execution {execution_id}")
            raise
        except Exception as e:
            logger.error(f"Error in execution stream for {execution_id}: {e}")
            raise

    @strawberry.subscription
    async def execution_events(
        self,
        info: strawberry.Info[GraphQLContext],
        execution_id: ExecutionID,
        event_types: Optional[List[EventType]] = None,
    ) -> AsyncGenerator[ExecutionEvent, None]:
        """Streams specific execution event types."""
        context: GraphQLContext = info.context
        state_store = context.state_store

        logger.info(f"Starting event stream subscription for {execution_id}")

        sequence = 0
        last_node_states = {}

        try:
            while True:
                # Get latest state
                state = await state_store.get_state(execution_id)

                if state:
                    current_node_states = state.node_states or {}

                    # Check for node status changes
                    for node_id, node_state in current_node_states.items():
                        old_state = last_node_states.get(node_id)

                        if not old_state or old_state.status != node_state.status:
                            sequence += 1
                            event_type = _get_event_type_for_node_status(
                                node_state.status
                            )

                            if event_types and event_type not in event_types:
                                continue

                            node_output = state.node_outputs.get(node_id)
                            output_value = node_output.value if node_output else None

                            yield ExecutionEvent(
                                execution_id=execution_id,
                                sequence=sequence,
                                event_type=event_type,
                                node_id=NodeID(node_id),
                                timestamp=node_state.ended_at
                                or node_state.started_at
                                or datetime.now().isoformat(),
                                data={
                                    "status": node_state.status.value,
                                    "output": output_value,
                                    "error": node_state.error,
                                },
                            )

                    # Update tracked states (deep copy to avoid serialization issues)
                    last_node_states = {
                        nid: ns for nid, ns in current_node_states.items()
                    }

                    if state.status in [
                        ExecutionStatus.COMPLETED,
                        ExecutionStatus.FAILED,
                        ExecutionStatus.ABORTED,
                    ]:
                        sequence += 1
                        final_event_type = {
                            ExecutionStatus.COMPLETED: EventType.EXECUTION_COMPLETED,
                            ExecutionStatus.FAILED: EventType.EXECUTION_FAILED,
                            ExecutionStatus.ABORTED: EventType.EXECUTION_ABORTED,
                        }.get(state.status, EventType.EXECUTION_UPDATE)

                        if not event_types or final_event_type in event_types:
                            yield ExecutionEvent(
                                execution_id=execution_id,
                                sequence=sequence,
                                event_type=final_event_type,
                                node_id=None,
                                timestamp=datetime.fromtimestamp(
                                    state.last_updated
                                ).isoformat(),
                                data={
                                    "status": state.status.value,
                                    "error": state.error,
                                },
                            )

                        logger.info(
                            f"Event stream completed for execution {execution_id}"
                        )
                        break

                # Poll interval (100ms)
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info(f"Event subscription cancelled for execution {execution_id}")
            raise
        except Exception as e:
            logger.error(f"Error in event stream for {execution_id}: {e}")
            raise

    @strawberry.subscription
    async def node_updates(
        self,
        info: strawberry.Info[GraphQLContext],
        execution_id: ExecutionID,
        node_types: Optional[List[NodeType]] = None,
    ) -> AsyncGenerator[NodeExecution, None]:
        """Streams node execution updates with optional filtering."""
        context: GraphQLContext = info.context
        state_store = context.state_store

        logger.info(f"Starting node updates subscription for {execution_id}")

        last_node_states = {}

        try:
            while True:
                # Get latest state
                state = await state_store.get_state(execution_id)

                if state:
                    # Check for node status changes
                    current_node_states = state.node_states or {}

                    for node_id, node_state in current_node_states.items():
                        old_state = last_node_states.get(node_id)

                        if not old_state or old_state.status != node_state.status:
                            node_type = NodeType.job

                            if node_types and node_type not in node_types:
                                continue

                            node_output = state.node_outputs.get(node_id)
                            output_value = node_output.value if node_output else None
                            tokens_used = None

                            if node_state.token_usage:
                                tokens_used = node_state.token_usage.total

                            yield NodeExecution(
                                execution_id=execution_id,
                                node_id=NodeID(node_id),
                                node_type=node_type,
                                status=node_state.status.value,
                                progress=None,
                                output=output_value,
                                error=node_state.error,
                                tokens_used=tokens_used,
                                timestamp=datetime.fromisoformat(
                                    node_state.ended_at
                                    or node_state.started_at
                                    or datetime.now().isoformat()
                                ),
                            )

                    # Update tracked states (deep copy to avoid serialization issues)
                    last_node_states = {
                        nid: ns for nid, ns in current_node_states.items()
                    }

                    # Check if execution is complete
                    if state.status in [
                        ExecutionStatus.COMPLETED,
                        ExecutionStatus.FAILED,
                        ExecutionStatus.ABORTED,
                    ]:
                        logger.info(
                            f"Node updates completed for execution {execution_id}"
                        )
                        break

                # Poll interval (100ms)
                await asyncio.sleep(0.1)

        except asyncio.CancelledError:
            logger.info(
                f"Node update subscription cancelled for execution {execution_id}"
            )
            raise
        except Exception as e:
            logger.error(f"Error in node update stream for {execution_id}: {e}")
            raise

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
