"""Standalone subscription resolver functions following the query pattern."""

import json
import logging
from collections.abc import AsyncGenerator
from datetime import datetime
from typing import Any

from strawberry.scalars import JSON

from dipeo.application.graphql.schema.base_subscription_resolver import BaseSubscriptionResolver
from dipeo.application.registry import ServiceRegistry
from dipeo.diagram_generated import Status
from dipeo.diagram_generated.domain_models import ExecutionID
from dipeo.diagram_generated.enums import EventType
from dipeo.diagram_generated.graphql.domain_types import ExecutionUpdate

logger = logging.getLogger(__name__)


def _transform_execution_update(event: dict[str, Any]) -> ExecutionUpdate | None:
    """Transform raw event to ExecutionUpdate type."""
    # Normalize timestamp to string
    timestamp = event.get("timestamp")
    if isinstance(timestamp, datetime):
        timestamp = timestamp.isoformat()
    elif isinstance(timestamp, int | float):
        # Convert numeric epoch timestamp to ISO string
        timestamp = datetime.fromtimestamp(timestamp).isoformat()
    elif timestamp is None or timestamp == "":
        timestamp = datetime.now().isoformat()
    else:
        # Ensure it's a string
        timestamp = str(timestamp)

    # Extract the event type, preferring UI event_type over raw type
    event_type = event.get("event_type") or event.get("type", "unknown")

    # Normalize execution_id key (handle both executionId and execution_id)
    exec_id_str = event.get("execution_id") or event.get("executionId", "")

    # For node events, restructure the data to match frontend expectations
    if event_type in ["NODE_STARTED", "NODE_COMPLETED", "NODE_FAILED"]:
        # node_id is at the top level of the event, not in data
        # data field contains the payload (node_type, output, etc.)
        event_data = event.get("data", {})

        # Handle None case explicitly
        if event_data is None:
            event_data = {}
        elif isinstance(event_data, str):
            try:
                event_data = json.loads(event_data)
            except Exception:
                event_data = {}

        # Extract node_id from top level, other fields from data payload
        data = {
            "node_id": event.get("node_id"),  # From top level
            "node_type": event_data.get("node_type"),  # From data payload
            "status": (
                "RUNNING"
                if event_type == "NODE_STARTED"
                else "COMPLETED"
                if event_type == "NODE_COMPLETED"
                else "FAILED"
            ),
            "output": event_data.get("output"),
            "metrics": event_data.get("metrics"),
            "error": event_data.get("error"),
        }
        # Remove None values
        data = {k: v for k, v in data.items() if v is not None}
    elif event_type == "NODE_STATUS_CHANGED":
        # Handle NODE_STATUS_CHANGED events
        # node_id and status are in the data payload
        event_data = event.get("data", {})
        if event_data is None:
            event_data = {}
        elif isinstance(event_data, str):
            try:
                event_data = json.loads(event_data)
            except Exception:
                event_data = {}

        # Extract node_id and status from data payload
        data = {
            "node_id": event_data.get("node_id"),  # From data payload
            "status": event_data.get("status"),  # From data payload
            "timestamp": event_data.get("timestamp") or event.get("timestamp"),
            **{k: v for k, v in event_data.items() if k not in ["node_id", "status", "timestamp"]},
        }
    elif event_type == "EXECUTION_STATUS_CHANGED":
        # Handle EXECUTION_STATUS_CHANGED events for execution start/stop
        data = event.get("data", {})
        if data is None:
            data = {}
        elif isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}
    elif event_type == "METRICS_COLLECTED":
        # Handle METRICS_COLLECTED events for real-time metrics updates
        data = event.get("data", {})
        if data is None:
            data = {}
        elif isinstance(data, str):
            try:
                data = json.loads(data)
            except Exception:
                data = {}
        # Ensure metrics data is properly structured
        if isinstance(data, dict) and "metrics" in data:
            data = data["metrics"]
    elif event_type == EventType.KEEPALIVE:
        # Handle keepalive events
        data = {"type": "keepalive"}
    else:
        # For other events, pass through the data as-is
        data = {k: v for k, v in event.items() if k not in ["type", "timestamp", "executionId"]}

    return ExecutionUpdate(
        execution_id=exec_id_str,
        event_type=event_type,
        data=data,  # Strawberry will handle JSON serialization
        timestamp=str(timestamp),
    )


def _filter_node_updates(event: dict[str, Any], node_id: str | None = None) -> bool:
    """Filter for node update events."""
    if event.get("type") not in [
        EventType.NODE_STATUS_CHANGED,
        EventType.NODE_PROGRESS,
    ]:
        return False

    if node_id:
        data = event.get("data", {})
        return data.get("node_id") == node_id

    return True


def _transform_node_update(event: dict[str, Any]) -> dict[str, Any] | None:
    """Transform node update event."""
    data = event.get("data", {})
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}
    return data


def _filter_interactive_prompts(event: dict[str, Any]) -> bool:
    """Filter for interactive prompt events."""
    return event.get("type") == EventType.INTERACTIVE_PROMPT


def _transform_interactive_prompt(event: dict[str, Any]) -> dict[str, Any] | None:
    """Transform interactive prompt event."""
    data = event.get("data", {})
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}
    return data


def _filter_execution_logs(event: dict[str, Any]) -> bool:
    """Filter for execution log events."""
    return event.get("type") == EventType.EXECUTION_LOG


def _transform_execution_log(event: dict[str, Any]) -> dict[str, Any] | None:
    """Transform execution log event."""
    data = event.get("data", {})
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except Exception:
            data = {}
    return data


async def execution_updates(
    registry: ServiceRegistry, execution_id: str
) -> AsyncGenerator[ExecutionUpdate]:
    """Subscribe to real-time updates for an execution."""
    resolver = BaseSubscriptionResolver(registry)

    # Special handling for execution updates with status checking
    exec_id = ExecutionID(str(execution_id))

    try:
        # Verify execution exists
        if not await resolver._verify_execution_exists(exec_id):
            return

        # Create subscription context
        event_queue, connection_id = await resolver._create_subscription_context(
            exec_id, "execution"
        )

        try:
            # Process events with custom transformation
            async for event in resolver._process_event_queue(
                event_queue,
                exec_id,
                event_filter=None,  # Accept all events for execution updates
                event_transformer=_transform_execution_update,
            ):
                if isinstance(event, ExecutionUpdate):
                    yield event
                elif (
                    isinstance(event, dict)
                    and event.get("event_type") == "EXECUTION_STATUS_CHANGED"
                ):
                    # Handle final status update from base class
                    yield ExecutionUpdate(
                        execution_id=event["execution_id"],
                        event_type=event["event_type"],
                        data=event["data"],
                        timestamp=event["timestamp"],
                    )

        finally:
            # Clean up
            await resolver._cleanup_subscription(connection_id, exec_id)

    except Exception as e:
        logger.error(f"Error in execution subscription: {e}")
        raise


async def node_updates(
    registry: ServiceRegistry, execution_id: str, node_id: str | None = None
) -> AsyncGenerator[JSON]:
    """Subscribe to node-specific updates within an execution."""
    resolver = BaseSubscriptionResolver(registry)

    async for event in resolver.subscribe(
        execution_id=execution_id,
        subscription_type="node",
        event_filter=lambda e: _filter_node_updates(e, node_id),
        event_transformer=_transform_node_update,
    ):
        yield event


async def interactive_prompts(registry: ServiceRegistry, execution_id: str) -> AsyncGenerator[JSON]:
    """Subscribe to interactive prompt requests."""
    resolver = BaseSubscriptionResolver(registry)

    async for event in resolver.subscribe(
        execution_id=execution_id,
        subscription_type="prompt",
        event_filter=_filter_interactive_prompts,
        event_transformer=_transform_interactive_prompt,
    ):
        yield event


async def execution_logs(registry: ServiceRegistry, execution_id: str) -> AsyncGenerator[JSON]:
    """Subscribe to execution log events."""
    resolver = BaseSubscriptionResolver(registry)

    async for event in resolver.subscribe(
        execution_id=execution_id,
        subscription_type="log",
        event_filter=_filter_execution_logs,
        event_transformer=_transform_execution_log,
    ):
        yield event
