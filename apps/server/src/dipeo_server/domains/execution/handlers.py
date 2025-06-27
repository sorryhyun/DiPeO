from __future__ import annotations

import functools
import logging
from enum import Enum
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Optional

from dipeo_domain.models import DomainNode, NodeExecutionStatus, NodeOutput as DomainNodeOutput
from dipeo_domain import NodeOutput

from .context import ExecutionContext

if TYPE_CHECKING:
    from .execution_view import NodeView

_log = logging.getLogger(__name__)

__all__ = [
    "DBOperation",
    "get_handlers",
    "node_handler",
]


class DBOperation(str, Enum):
    LOAD = "LOAD"
    SAVE = "SAVE"
    APPEND = "APPEND"


_HandlerFn = Callable[[DomainNode, ExecutionContext], Awaitable[NodeOutput]]
_handlers: Dict[str, _HandlerFn] = {}


def _wrap_with_state(node_type: str, func: _HandlerFn) -> _HandlerFn:
    """Return a wrapper that transparently manages node‑status lifecycle."""

    @functools.wraps(func)
    async def _wrapped(
        node: DomainNode, context: ExecutionContext, **kwargs: Any
    ) -> NodeOutput:  # type: ignore[override]
        await context.state_store.update_node_status(
            context.execution_id, node.id, NodeExecutionStatus.RUNNING
        )
        try:
            output = await func(node, context, **kwargs)
            await context.state_store.update_node_status(
                context.execution_id, node.id, NodeExecutionStatus.COMPLETED, output
            )
            return output
        except Exception as exc:  # pylint: disable=broad-except
            _log.exception(
                "%s node %s failed", node_type.upper(), node.id, exc_info=exc
            )
            error_output = create_node_output({}, {"error": str(exc)})
            await context.state_store.update_node_status(
                context.execution_id, node.id, NodeExecutionStatus.FAILED, error_output
            )
            return error_output

    # Store the original function for signature inspection
    _wrapped.__wrapped__ = func
    return _wrapped


def node_handler(node_type: str) -> Callable[[_HandlerFn], _HandlerFn]:
    """Decorator that registers a node handler and injects status tracking."""

    def decorator(func: _HandlerFn) -> _HandlerFn:
        _handlers[node_type] = _wrap_with_state(node_type, func)
        return func

    return decorator


def get_handlers() -> Dict[str, _HandlerFn]:
    """Return a *copy* of the internal handler registry."""
    return _handlers.copy()


def create_node_output(
    value: Dict[str, Any] | None = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> NodeOutput:
    """Utility to save a few keystrokes when constructing outputs."""

    return NodeOutput(value=value or {}, metadata=metadata)


async def _edge_inputs(
    node: DomainNode,
    context: ExecutionContext,
    *,
    as_dict: bool = True,
    node_view: "NodeView",
) -> Dict[str, Any]:
    """Collect downstream values from all incoming edges.

    Returned mapping keys are the *edge labels* (defaulting to "default").
    If *as_dict* is False, only the first matching payload is returned.
    """

    results = node_view.get_active_inputs()
    if not as_dict and results:
        return next(iter(results.values()), None)
    return results


@node_handler("start")
async def execute_start(node: DomainNode, context: ExecutionContext) -> NodeOutput:
    """Kick‑off node: no input, always succeeds."""
    return create_node_output({"default": ""}, {"message": "Execution started"})


@node_handler("person_job")
async def execute_person_job(
    node: DomainNode, context: ExecutionContext, node_view: Optional["NodeView"] = None
) -> NodeOutput:
    """Handle conversational person_job node using domain service."""
    # Collect inputs from edges
    inputs = await _edge_inputs(node, context, node_view=node_view)

    # Delegate to conversation service
    result = await context.conversation_service.execute_person_job(
        node=node,
        execution_id=context.execution_id,
        exec_count=context.exec_counts.get(node.id, 0),
        inputs=inputs,
        diagram=context.diagram,
        llm_service=context.llm_service,
    )

    # Handle token usage accumulation
    if result.get("token_usage"):
        context.add_token_usage(node.id, result["token_usage"])

    return create_node_output(result["output_values"], result["metadata"])


@node_handler("endpoint")
async def execute_endpoint(
    node: DomainNode, context: ExecutionContext, node_view: Optional["NodeView"] = None
) -> NodeOutput:
    """Endpoint node – pass through data and optionally save to file."""

    data = node.data or {}

    if (direct := data.get("data")) is not None:
        result_data = direct
    else:
        collected = await _edge_inputs(node, context, node_view=node_view)
        result_data = collected if collected else {}

    save_to_file = data.get("saveToFile", False) or data.get("save_to_file", False)
    if save_to_file:
        file_path = (
            data.get("filePath") or data.get("fileName") or data.get("file_name")
        )

        if file_path:
            try:
                if isinstance(result_data, dict) and "default" in result_data:
                    content = str(result_data["default"])
                else:
                    content = str(result_data)

                await context.file_service.write(file_path, content)
                _log.info(f"Saved endpoint result to {file_path}")

                return create_node_output(
                    {"default": result_data}, {"saved_to": file_path}
                )
            except Exception as exc:
                _log.error(f"Failed to save endpoint result to {file_path}: {exc}")
                return create_node_output(
                    {"default": result_data}, {"save_error": str(exc)}
                )
        else:
            _log.warning("saveToFile is true but no file path provided")

    return create_node_output({"default": result_data})


@node_handler("condition")
async def execute_condition(
    node: DomainNode, context: ExecutionContext, node_view: Optional["NodeView"] = None
) -> NodeOutput:
    """Condition node: currently supports *detect_max_iterations*."""

    data = node.data or {}
    condition_type: str = data.get("conditionType", "")

    if condition_type != "detect_max_iterations":
        return create_node_output({"False": None}, {"condition_result": False})

    # True only if *all* upstream person_job nodes reached their max_iterations
    result = True
    for edge in context.find_edges_to(node.id):
        src_node_id = edge.source.split(":")[0]
        src_node = next((n for n in context.diagram.nodes if n.id == src_node_id), None)
        if src_node and src_node.type == "person_job":
            exec_count = context.exec_counts.get(src_node_id, 0)
            max_iter = int((src_node.data or {}).get("maxIteration", 1))
            if exec_count < max_iter:
                result = False
                break

    # Collect all incoming payloads and forward them unchanged
    inputs = await _edge_inputs(node, context, as_dict=True, node_view=node_view)

    # Forward inputs with branch key for backward compatibility
    branch_key = "True" if result else "False"
    value: Dict[str, Any] = {**inputs}
    value[branch_key] = inputs

    if "default" not in value and inputs:
        if "conversation" in inputs:
            value["default"] = inputs["conversation"]
        else:
            first_key = next(iter(inputs.keys()), None)
            if first_key:
                value["default"] = inputs[first_key]

    _log.debug(
        "Condition node %s outputting %s branch with keys: %s",
        node.id,
        branch_key,
        list(value.keys()),
    )

    return create_node_output(value, {"condition_result": result})


@node_handler("db")
async def execute_db(
    node: DomainNode, context: ExecutionContext, node_view: Optional["NodeView"] = None
) -> NodeOutput:
    """File‑based DB node supporting *read*, *write* and *append* operations."""

    data = node.data or {}
    operation = data.get("operation", "read")
    file_path = data.get("sourceDetails", "")

    input_val = await _edge_inputs(node, context, as_dict=False, node_view=node_view)

    try:
        if operation == "read":
            if hasattr(context.file_service, "aread"):
                result = await context.file_service.aread(file_path)
            else:
                result = context.file_service.read(file_path)
        elif operation == "write":
            await context.file_service.write(file_path, str(input_val))
            result = f"Saved to {file_path}"
        elif operation == "append":
            existing = ""
            if hasattr(context.file_service, "aread"):
                try:
                    existing = await context.file_service.aread(file_path)
                except Exception:
                    pass
            await context.file_service.write(file_path, existing + str(input_val))
            result = f"Appended to {file_path}"
        else:
            result = "Unknown operation"
    except Exception as exc:
        _log.warning("DB op %s failed: %s", operation, exc)
        result = f"Error: {exc}"

    return create_node_output({"default": result, "topic": result})


@node_handler("notion")
async def execute_notion(
    node: DomainNode, context: ExecutionContext, node_view: Optional["NodeView"] = None
) -> NodeOutput:
    """Wrapper around `context.notion_service.execute_action`."""

    data = node.data or {}
    action = data.get("action", "read")
    database_id = data.get("database_id", "")
    payload = await _edge_inputs(node, context, node_view=node_view)

    result = await context.notion_service.execute_action(
        action=action,
        database_id=database_id,
        data=payload,
    )
    return create_node_output({"default": result})
