from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional

from dipeo_domain.models import DomainNode, NodeExecutionStatus, NodeOutput

from .context import ExecutionContext

_log = logging.getLogger(__name__)

__all__ = [
    "DBOperation",
    "node_handler",
    "get_handlers",
]


class DBOperation(str, Enum):
    LOAD = "LOAD"
    SAVE = "SAVE"
    APPEND = "APPEND"


# Generic decorator / registry utilities                                     #


_HandlerFn = Callable[[DomainNode, ExecutionContext], Awaitable[NodeOutput]]
_handlers: Dict[str, _HandlerFn] = {}


def _wrap_with_state(node_type: str, func: _HandlerFn) -> _HandlerFn:  # noqa: D401
    """Return a wrapper that transparently manages node‑status lifecycle."""

    async def _wrapped(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:  # type: ignore[override]
        await ctx.state_store.update_node_status(
            ctx.execution_id, node.id, NodeExecutionStatus.RUNNING
        )
        try:
            output = await func(node, ctx)
            await ctx.state_store.update_node_status(
                ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output
            )
            return output
        except Exception as exc:  # pylint: disable=broad-except
            _log.exception("%s node %s failed", node_type.upper(), node.id, exc_info=exc)
            error_output = create_node_output({}, {"error": str(exc)})
            await ctx.state_store.update_node_status(
                ctx.execution_id, node.id, NodeExecutionStatus.FAILED, error_output
            )
            return error_output

    _wrapped.__name__ = func.__name__  # keep tooling happy
    return _wrapped


def node_handler(node_type: str) -> Callable[[_HandlerFn], _HandlerFn]:
    """Decorator that registers a node handler and injects status tracking."""

    def decorator(func: _HandlerFn) -> _HandlerFn:
        _handlers[node_type] = _wrap_with_state(node_type, func)
        return func  # func is returned unwrapped for type checkers/tests

    return decorator


def get_handlers() -> Dict[str, _HandlerFn]:
    """Return a *copy* of the internal handler registry."""
    # Provide the *wrapped* callables – the engine never needs the raw ones.
    return {k: _wrap_with_state(k, v) for k, v in _handlers.items()}


# Tiny helpers shared by multiple handlers                                    #


def create_node_output(  # noqa: D401
    value: Dict[str, Any] | None = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> NodeOutput:
    """Utility to save a few keystrokes when constructing outputs."""

    return NodeOutput(value=value or {}, metadata=metadata or {})


async def _edge_inputs(
    node: DomainNode,
    ctx: ExecutionContext,
    *,
    as_dict: bool = True,
) -> Dict[str, Any]:
    """Collect downstream values from all incoming edges.

    Returned mapping keys are the *edge labels* (defaulting to "default").
    If *as_dict* is False, only the first matching payload is returned.
    """

    results: Dict[str, Any] = {}
    for edge in ctx.find_edges_to(node.id):
        src_id = edge.source.split(":")[0]
        from_output = ctx.get_node_output(src_id)
        if not from_output:
            _log.warning("No output for source node %s → %s", src_id, node.id)
            continue
        label = edge.data.get("label", "default") if edge.data else "default"
        if label in from_output.value:
            results[label] = from_output.value[label]
        else:
            _log.warning(
                "Edge label '%s' missing in output from %s (keys=%s)",
                label,
                src_id,
                list(from_output.value.keys()),
            )
    if as_dict:
        return results
    return next(iter(results.values()), None)  # type: ignore[return-value]


# Concrete node handlers                                                      #


@node_handler("start")
async def execute_start(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:  # noqa: D401
    """Kick‑off node: no input, always succeeds."""
    return create_node_output({"default": ""}, {"message": "Execution started"})


@node_handler("person_job")
async def execute_person_job(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:  # noqa: C901, D401 – complex but now self‑contained
    """Handle conversational *person_job* node with minimal boilerplate.

    This keeps the original behaviour (first‑turn prompt, default prompt,
    judge‑panel aggregation, forgetting modes, …) but relies on helpers for
    edge traversal and status updates.
    """

    exec_count = ctx.exec_counts.get(node.id, 0)
    data = node.data or {}

    person_id: Optional[str] = data.get("personId")
    first_only_prompt: str = data.get("firstOnlyPrompt", "")
    default_prompt: str = data.get("defaultPrompt", "")
    max_iteration: int = int(data.get("maxIteration", 1))
    forgetting_mode: Optional[str] = data.get("forgettingMode")
    is_judge: bool = "judge" in data.get("label", "").lower()

    # Conversation history ---------------------------------------------------
    conversation = ctx.get_conversation_history(person_id) if person_id else []

    if forgetting_mode == "on_every_turn" and exec_count > 1:
        conversation = [m for m in conversation if m.get("role") in {"system", "user"}]

    # Ensure system prompt present
    if not conversation or conversation[0].get("role") != "system":
        person_obj = next((p for p in ctx.diagram.persons if p.id == person_id), None) if person_id else None
        system_prompt = (
            getattr(person_obj, "system_prompt", None)
            or getattr(person_obj, "systemPrompt", "")
        ) if person_obj else ""
        conversation.insert(0, {"role": "system", "content": system_prompt})

    # Gather edge inputs -----------------------------------------------------
    inputs = await _edge_inputs(node, ctx)

    if "conversation" in inputs and exec_count > 1:
        conversation.append({"role": "user", "content": inputs["conversation"]})

    if exec_count == 1 and first_only_prompt:
        prompt = first_only_prompt.format(**inputs)
    else:
        prompt = default_prompt

    # Judge nodes collect debates from other person_job panels ---------------
    if is_judge:
        debate_context: list[str] = []
        for other_node in ctx.diagram.nodes:
            if other_node.type != "person_job" or other_node.id == node.id:
                continue
            other_pid = other_node.data.get("personId") if other_node.data else None
            other_conv = ctx.get_conversation_history(other_pid) if other_pid else []
            if not other_conv:
                continue
            label = other_node.data.get("label", other_node.id) if other_node.data else other_node.id
            debate_messages = [m for m in other_conv if m.get("role") != "system"]
            if not debate_messages:
                continue
            debate_context.append(f"\n{label}:\n")
            for msg in debate_messages:
                role, content = msg.get("role"), msg.get("content", "")
                debate_context.append(f"{'Input' if role == 'user' else 'Response'}: {content}\n")
        if debate_context:
            debate_txt = "Here are the arguments from different panels:\n" + "".join(debate_context) + "\n\n"
            prompt = debate_txt + (prompt or "Based on the above arguments, judge which panel is more reasonable.")

    if prompt:
        conversation.append({"role": "user", "content": prompt})

    # Call LLM ---------------------------------------------------------------
    person_obj = next((p for p in ctx.diagram.persons if p.id == person_id), None) if person_id else None
    person_cfg = {
        "service": getattr(person_obj, "service", "openai"),
        "api_key_id": getattr(person_obj, "api_key_id", None) or getattr(person_obj, "apiKeyId", None),
        "model": getattr(person_obj, "model", "gpt-4.1-nano"),
    }

    llm_result = await ctx.llm_service.call_llm(
        service=person_cfg["service"],
        api_key_id=person_cfg["api_key_id"],
        model=person_cfg["model"],
        messages=conversation,
    )

    response_text: str = llm_result.get("response", "")
    token_usage: int = llm_result.get("token_usage") or len(response_text.split())

    ctx.add_to_conversation(person_id, {"role": "assistant", "content": response_text})

    return create_node_output(
        {"default": response_text},
        {"model": person_cfg["model"], "tokens_used": token_usage},
    )


@node_handler("endpoint")
async def execute_endpoint(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:  # noqa: D401
    """Endpoint node – pass through explicit *data* or collected edge inputs."""

    if (direct := (node.data or {}).get("data")) is not None:
        return create_node_output({"default": direct})

    collected = await _edge_inputs(node, ctx)
    return create_node_output({"default": collected} if collected else {})


@node_handler("condition")
async def execute_condition(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:  # noqa: D401
    """Condition node: currently supports *detect_max_iterations*."""

    data = node.data or {}
    condition_type: str = data.get("conditionType", "")

    if condition_type != "detect_max_iterations":
        return create_node_output({"False": None}, {"condition_result": False})

    # True only if *all* upstream person_job nodes reached their max_iterations
    result = True
    for edge in ctx.find_edges_to(node.id):
        src_node_id = edge.source.split(":")[0]
        src_node = next((n for n in ctx.diagram.nodes if n.id == src_node_id), None)
        if src_node and src_node.type == "person_job":
            exec_count = ctx.exec_counts.get(src_node_id, 0)
            max_iter = int((src_node.data or {}).get("maxIteration", 1))
            if exec_count < max_iter:
                result = False
                break
    input_val = await _edge_inputs(node, ctx, as_dict=False)
    return create_node_output({"True" if result else "False": input_val}, {"condition_result": result})


@node_handler("db")
async def execute_db(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:  # noqa: D401
    """File‑based DB node supporting *read*, *write* and *append* operations."""

    data = node.data or {}
    operation = data.get("operation", "read")
    file_path = data.get("sourceDetails", "")

    # For write/append we need input data from edges
    input_val = await _edge_inputs(node, ctx, as_dict=False)

    try:
        if operation == "read":
            # Prefer async if available
            if hasattr(ctx.file_service, "aread"):
                result = await ctx.file_service.aread(file_path)
            else:
                result = ctx.file_service.read(file_path)
        elif operation == "write":
            await ctx.file_service.write(file_path, str(input_val))
            result = f"Saved to {file_path}"
        elif operation == "append":
            existing = ""
            if hasattr(ctx.file_service, "aread"):
                try:
                    existing = await ctx.file_service.aread(file_path)
                except Exception:  # file may not exist yet
                    pass
            await ctx.file_service.write(file_path, existing + str(input_val))
            result = f"Appended to {file_path}"
        else:
            result = "Unknown operation"
    except Exception as exc:  # noqa: PERF203
        _log.warning("DB op %s failed: %s", operation, exc)
        result = f"Error: {exc}"

    return create_node_output({"default": result, "topic": result})


@node_handler("notion")
async def execute_notion(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:  # noqa: D401
    """Wrapper around `ctx.notion_service.execute_action`."""

    data = node.data or {}
    action = data.get("action", "read")
    database_id = data.get("database_id", "")
    payload = await _edge_inputs(node, ctx)

    result = await ctx.notion_service.execute_action(
        action=action,
        database_id=database_id,
        data=payload,
    )
    return create_node_output({"default": result})
