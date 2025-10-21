"""Execution-related query resolvers."""

import asyncio
import logging
from datetime import datetime

import strawberry
from strawberry.scalars import JSON

from dipeo.application.execution.observers import MetricsObserver
from dipeo.application.registry import ServiceRegistry
from dipeo.application.registry.keys import STATE_STORE, ServiceKey
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import Status
from dipeo.diagram_generated.domain_models import DiagramID, ExecutionID
from dipeo.diagram_generated.graphql.domain_types import ExecutionStateType
from dipeo.diagram_generated.graphql.inputs import ExecutionFilterInput

logger = get_module_logger(__name__)


async def get_execution(
    registry: ServiceRegistry, execution_id: strawberry.ID
) -> ExecutionStateType | None:
    """Get a single execution by ID."""
    try:
        state_store = registry.resolve(STATE_STORE)
        execution_id_typed = ExecutionID(str(execution_id))
        execution = await state_store.get_state(str(execution_id_typed))

        if not execution:
            return None

        return ExecutionStateType.from_pydantic(execution)

    except Exception as e:
        logger.error(f"Error fetching execution {execution_id}: {e}")
        return None


async def list_executions(
    registry: ServiceRegistry,
    filter: ExecutionFilterInput | None = None,
    limit: int = 100,
    offset: int = 0,
) -> list[ExecutionStateType]:
    """List executions with optional filtering."""
    try:
        state_store = registry.resolve(STATE_STORE)
        executions = await state_store.list_executions(
            diagram_id=filter.diagram_id if filter else None,
            status=filter.status if filter else None,
            limit=limit,
            offset=offset,
        )

        return [ExecutionStateType.from_pydantic(state) for state in executions]

    except Exception as e:
        logger.error(f"Error listing executions: {e}")
        return []


async def get_execution_order(registry: ServiceRegistry, execution_id: strawberry.ID) -> JSON:
    """Get the execution order for a given execution."""
    state_store = registry.resolve(STATE_STORE)
    execution_id_typed = ExecutionID(str(execution_id))

    # For active executions, prefer cache to get the freshest data
    execution = None
    if hasattr(state_store, "get_state_from_cache"):
        execution = await state_store.get_state_from_cache(str(execution_id_typed))

    # If not in cache, try regular get_state with retry logic for race conditions
    if not execution:
        for attempt in range(5):
            execution = await state_store.get_state(str(execution_id_typed))
            if execution:
                break
            if attempt < 4:
                await asyncio.sleep(0.05 * (2**attempt))

    # If execution is RUNNING but has no executed nodes yet, wait for events to be processed
    if execution and execution.status == Status.RUNNING and not execution.executed_nodes:
        for _ in range(3):
            await asyncio.sleep(0.1)
            if hasattr(state_store, "get_state_from_cache"):
                fresh_execution = await state_store.get_state_from_cache(str(execution_id_typed))
                if fresh_execution and fresh_execution.executed_nodes:
                    execution = fresh_execution
                    break

    if not execution:
        return {
            "executionId": str(execution_id_typed),
            "nodes": [],
            "error": "Execution not found",
            "status": "NOT_FOUND",
            "totalNodes": 0,
        }

    nodes = []
    executed_nodes = execution.executed_nodes if hasattr(execution, "executed_nodes") else []
    node_states = execution.node_states if hasattr(execution, "node_states") else {}

    for node_id in executed_nodes:
        if node_id in node_states:
            node_state = node_states[node_id]

            node_step = {
                "nodeId": node_id,
                "nodeName": node_id,
                "status": node_state.status.name if hasattr(node_state, "status") else "UNKNOWN",
            }

            if hasattr(node_state, "started_at") and node_state.started_at:
                node_step["startedAt"] = node_state.started_at

            if hasattr(node_state, "ended_at") and node_state.ended_at:
                node_step["endedAt"] = node_state.ended_at

                if hasattr(node_state, "started_at") and node_state.started_at:
                    try:
                        start = datetime.fromisoformat(node_state.started_at.replace("Z", "+00:00"))
                        end = datetime.fromisoformat(node_state.ended_at.replace("Z", "+00:00"))
                        duration_ms = int((end - start).total_seconds() * 1000)
                        node_step["duration"] = duration_ms
                    except Exception:
                        pass

            if hasattr(node_state, "error") and node_state.error:
                node_step["error"] = node_state.error

            if hasattr(node_state, "token_usage") and node_state.token_usage:
                token_usage = node_state.token_usage
                node_step["tokenUsage"] = {
                    "input": token_usage.input_tokens
                    if hasattr(token_usage, "input_tokens")
                    else 0,
                    "output": token_usage.output_tokens
                    if hasattr(token_usage, "output_tokens")
                    else 0,
                    "cached": token_usage.cached_tokens
                    if hasattr(token_usage, "cached_tokens")
                    else 0,
                    "total": token_usage.total_tokens
                    if hasattr(token_usage, "total_tokens")
                    else 0,
                }

            nodes.append(node_step)

    result = {
        "executionId": str(execution_id_typed),
        "status": execution.status.name if hasattr(execution, "status") else "UNKNOWN",
        "nodes": nodes,
        "totalNodes": len(nodes),
    }

    if hasattr(execution, "started_at") and execution.started_at:
        result["startedAt"] = execution.started_at

    if hasattr(execution, "ended_at") and execution.ended_at:
        result["endedAt"] = execution.ended_at

    return result


async def get_execution_metrics(
    registry: ServiceRegistry, execution_id: strawberry.ID
) -> JSON | None:
    """Get metrics for a given execution."""
    state_store = registry.resolve(STATE_STORE)
    execution_id_typed = ExecutionID(str(execution_id))

    try:
        metrics_observer_key = ServiceKey[MetricsObserver]("metrics_observer")
        metrics_observer = registry.resolve(metrics_observer_key)

        metrics_summary = metrics_observer.get_metrics_summary(str(execution_id))
        if metrics_summary:
            execution_metrics = metrics_observer.get_execution_metrics(str(execution_id))
            if execution_metrics:
                node_breakdown = []
                for node_id, node_metrics in execution_metrics.node_metrics.items():
                    node_data = {
                        "node_id": node_id,
                        "node_type": node_metrics.node_type,
                        "duration_ms": node_metrics.duration_ms,
                        "token_usage": node_metrics.token_usage
                        or {"input": 0, "output": 0, "total": 0},
                        "error": node_metrics.error,
                    }
                    node_breakdown.append(node_data)

                metrics_summary["node_breakdown"] = node_breakdown

            return metrics_summary
    except Exception:
        pass

    execution = await state_store.get_state(str(execution_id_typed))
    if not execution or not hasattr(execution, "metrics"):
        return {}

    return execution.metrics or {}


async def get_execution_history(
    registry: ServiceRegistry,
    diagram_id: strawberry.ID | None = None,
    limit: int = 100,
    include_metrics: bool = False,
) -> list[ExecutionStateType]:
    """Get execution history with optional filtering."""
    try:
        state_store = registry.resolve(STATE_STORE)
        filter_input = None
        if diagram_id:
            filter_input = ExecutionFilterInput(diagram_id=DiagramID(str(diagram_id)))

        executions = await state_store.list_executions(
            diagram_id=filter_input.diagram_id if filter_input else None,
            status=filter_input.status if filter_input else None,
            limit=limit,
            offset=0,
        )

        if not include_metrics:
            for execution in executions:
                if hasattr(execution, "metrics"):
                    execution.metrics = None

        return [ExecutionStateType.from_pydantic(execution) for execution in executions]

    except Exception as e:
        logger.error(f"Error getting execution history: {e}")
        return []
