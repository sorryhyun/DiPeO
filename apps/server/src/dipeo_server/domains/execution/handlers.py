from __future__ import annotations

import logging
from enum import Enum
from typing import Any, Awaitable, Callable, Dict, Optional

from dipeo_domain.models import DomainNode, NodeExecutionStatus, NodeOutput

from .context import ExecutionContext

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
            _log.exception(
                "%s node %s failed", node_type.upper(), node.id, exc_info=exc
            )
            error_output = create_node_output({}, {"error": str(exc)})
            await ctx.state_store.update_node_status(
                ctx.execution_id, node.id, NodeExecutionStatus.FAILED, error_output
            )
            return error_output

    _wrapped.__name__ = func.__name__
    return _wrapped


def node_handler(node_type: str) -> Callable[[_HandlerFn], _HandlerFn]:
    """Decorator that registers a node handler and injects status tracking."""

    def decorator(func: _HandlerFn) -> _HandlerFn:
        _handlers[node_type] = _wrap_with_state(node_type, func)
        return func

    return decorator


def get_handlers() -> Dict[str, _HandlerFn]:
    """Return a *copy* of the internal handler registry."""
    return {k: _wrap_with_state(k, v) for k, v in _handlers.items()}


def create_node_output(
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

        src_node = next((n for n in ctx.diagram.nodes if n.id == src_id), None)
        if src_node and src_node.type == "condition":
            condition_result = from_output.metadata.get("condition_result", False)
            edge_branch = edge.data.get("branch", None) if edge.data else None

            if edge_branch is not None:
                edge_branch_bool = edge_branch.lower() == "true"
                if edge_branch_bool != condition_result:
                    continue

        label = edge.data.get("label", "default") if edge.data else "default"

        if src_node and src_node.type == "condition":
            source_handle = edge.source.split(":")[1] if ":" in edge.source else "default"

            if label in from_output.value:
                results[label] = from_output.value[label]
            elif label == "default" and source_handle in from_output.value:
                results[label] = from_output.value[source_handle]
            elif "conversation" in from_output.value and label == "default":
                results[label] = from_output.value["conversation"]
            elif "default" in from_output.value:
                results[label] = from_output.value["default"]
            else:
                _log.warning(
                    "Edge label '%s' missing in output from condition node %s (keys=%s)",
                    label,
                    src_id,
                    list(from_output.value.keys()),
                )
        else:
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


@node_handler("start")
async def execute_start(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    """Kick‑off node: no input, always succeeds."""
    return create_node_output({"default": ""}, {"message": "Execution started"})


@node_handler("person_job")
async def execute_person_job(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    """Handle conversational *person_job* node with minimal boilerplate.

    This keeps the original behaviour (first‑turn prompt, default prompt,
    judge‑panel aggregation, forgetting modes, …) but relies on helpers for
    edge traversal and status updates.
    """

    exec_count = ctx.exec_counts.get(node.id, 0)
    data = node.data or {}

    person_id: Optional[str] = data.get("personId") or data.get("person")
    first_only_prompt: str = data.get("firstOnlyPrompt", "")
    default_prompt: str = data.get("defaultPrompt", "")
    max_iteration: int = int(data.get("maxIteration", 1))
    forgetting_mode: Optional[str] = data.get("forgettingMode")
    is_judge: bool = "judge" in data.get("label", "").lower()

    conversation = ctx.get_conversation_history(person_id) if person_id else []

    if forgetting_mode == "on_every_turn" and exec_count > 1:
        conversation = [m for m in conversation if m.get("role") in {"system", "user"}]

    # Ensure system prompt present
    if not conversation or conversation[0].get("role") != "system":
        person_obj = (
            next((p for p in ctx.diagram.persons if p.id == person_id), None)
            if person_id
            else None
        )
        system_prompt = (
            (
                getattr(person_obj, "system_prompt", None)
                or getattr(person_obj, "systemPrompt", "")
            )
            if person_obj
            else ""
        )
        conversation.insert(
            0, {"role": "system", "content": system_prompt, "personId": person_id}
        )

    inputs = await _edge_inputs(node, ctx)

    if "conversation" in inputs:
        upstream_conv = inputs["conversation"]
        if isinstance(upstream_conv, list) and upstream_conv:
            # Check if we're in a conversation loop by looking for our own messages
            our_messages_count = sum(
                1 for msg in upstream_conv
                if msg.get("personId") == person_id and msg.get("role") == "assistant"
            )

            if our_messages_count > 0:
                _log.debug(
                    "Detected conversation loop for %s - found %d of our messages",
                    person_id,
                    our_messages_count
                )
                last_other_exchange = []
                for i in range(len(upstream_conv) - 1, -1, -1):
                    msg = upstream_conv[i]
                    if msg.get("personId") == person_id or msg.get("role") == "system":
                        continue
                    if msg.get("role") in ["user", "assistant"]:
                        last_other_exchange.append(msg)
                        if len(last_other_exchange) >= 1 and msg.get("role") == "assistant":
                            break

                if last_other_exchange:
                    last_msg = last_other_exchange[0]
                    content_exists = any(
                        msg.get("content") == last_msg.get("content")
                        for msg in conversation
                    )

                    if not content_exists:
                        conversation.append({
                            "role": "user",
                            "content": last_msg.get("content", ""),
                            "personId": person_id,
                            "source": f"from_{last_msg.get('personId', 'unknown')}"
                        })
            else:
                # Not in a loop - use original logic for first iteration
                # Extract the last user/assistant exchange from upstream conversation
                last_exchange = []
                for msg in reversed(upstream_conv):
                    if msg.get("role") in ["user", "assistant"]:
                        last_exchange.append(msg)
                        if len(last_exchange) == 2:  # Got both user and assistant
                            break

                # Add the upstream conversation context as a user message
                if last_exchange:
                    # Format the upstream exchange as context
                    context_parts = []
                    for msg in reversed(last_exchange):
                        role = "Input" if msg.get("role") == "user" else "Response"
                        context_parts.append(f"{role}: {msg.get('content', '')}")

                    upstream_text = "\n".join(context_parts)
                    conversation.append(
                        {"role": "user", "content": upstream_text, "personId": person_id}
                    )

    if exec_count == 1 and first_only_prompt:
        # Convert {{var}} to {var} for Python format()
        prompt_template = first_only_prompt.replace("{{", "{").replace("}}", "}")
        prompt = prompt_template.format(**inputs)
    else:
        prompt = default_prompt

    if is_judge:
        debate_context: list[str] = []
        for other_node in ctx.diagram.nodes:
            if other_node.type != "person_job" or other_node.id == node.id:
                continue
            other_pid = other_node.data.get("personId") if other_node.data else None
            other_conv = ctx.get_conversation_history(other_pid) if other_pid else []
            if not other_conv:
                continue
            label = (
                other_node.data.get("label", other_node.id)
                if other_node.data
                else other_node.id
            )
            debate_messages = [m for m in other_conv if m.get("role") != "system"]
            if not debate_messages:
                continue
            debate_context.append(f"\n{label}:\n")
            for msg in debate_messages:
                role, content = msg.get("role"), msg.get("content", "")
                debate_context.append(
                    f"{'Input' if role == 'user' else 'Response'}: {content}\n"
                )
        if debate_context:
            debate_txt = (
                "Here are the arguments from different panels:\n"
                + "".join(debate_context)
                + "\n\n"
            )
            prompt = debate_txt + (
                prompt
                or "Based on the above arguments, judge which panel is more reasonable."
            )

    if prompt:
        conversation.append({"role": "user", "content": prompt, "personId": person_id})

    person_obj = (
        next((p for p in ctx.diagram.persons if p.id == person_id), None)
        if person_id
        else None
    )
    person_cfg = {
        "service": getattr(person_obj, "service", "openai"),
        "api_key_id": getattr(person_obj, "api_key_id", None)
        or getattr(person_obj, "apiKeyId", None),
        "model": getattr(person_obj, "model", "gpt-4.1-nano"),
    }

    llm_result = await ctx.llm_service.call_llm(
        service=person_cfg["service"],
        api_key_id=person_cfg["api_key_id"],
        model=person_cfg["model"],
        messages=conversation,
    )

    response_text: str = llm_result.get("response", "")
    token_usage_obj = llm_result.get("token_usage")

    # Extract total token count from TokenUsage object
    if token_usage_obj and hasattr(token_usage_obj, "total"):
        token_usage: int = token_usage_obj.total
    else:
        # Fallback to word count if no token usage available
        token_usage: int = len(response_text.split())

    ctx.add_to_conversation(
        person_id,
        {"role": "assistant", "content": response_text, "personId": person_id},
    )

    output_values = {"default": response_text}

    for edge in ctx.diagram.arrows:
        if edge.source.startswith(node.id + ":"):
            edge_data = edge.data if edge.data and isinstance(edge.data, dict) else {}
            if edge_data.get("contentType") == "conversation_state":
                conv_history = ctx.get_conversation_history(person_id) if person_id else []
                output_values["conversation"] = conv_history
                break

    # Prepare token usage metadata in the expected format
    token_usage_metadata = {}
    if token_usage_obj and hasattr(token_usage_obj, "__dict__"):
        # Convert TokenUsage object to dict
        token_usage_metadata = {
            "input": getattr(token_usage_obj, "input", 0),
            "output": getattr(token_usage_obj, "output", 0),
            "total": getattr(token_usage_obj, "total", token_usage),
        }
        if hasattr(token_usage_obj, "cached"):
            token_usage_metadata["cached"] = token_usage_obj.cached
    else:
        # Fallback for simple token count
        token_usage_metadata = {
            "input": 0,
            "output": token_usage,
            "total": token_usage,
        }

    return create_node_output(
        output_values,
        {
            "model": person_cfg["model"],
            "tokens_used": token_usage,  # Keep for backward compatibility
            "tokenUsage": token_usage_metadata  # Add proper format for state registry
        },
    )


@node_handler("endpoint")
async def execute_endpoint(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    """Endpoint node – pass through data and optionally save to file."""

    data = node.data or {}

    if (direct := data.get("data")) is not None:
        result_data = direct
    else:
        collected = await _edge_inputs(node, ctx)
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

                await ctx.file_service.write(file_path, content)
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
async def execute_condition(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
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

    # Collect all incoming payloads and forward them unchanged
    inputs = await _edge_inputs(node, ctx, as_dict=True)

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
        list(value.keys())
    )

    return create_node_output(value, {"condition_result": result})


@node_handler("db")
async def execute_db(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    """File‑based DB node supporting *read*, *write* and *append* operations."""

    data = node.data or {}
    operation = data.get("operation", "read")
    file_path = data.get("sourceDetails", "")

    input_val = await _edge_inputs(node, ctx, as_dict=False)

    try:
        if operation == "read":
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
                except Exception:
                    pass
            await ctx.file_service.write(file_path, existing + str(input_val))
            result = f"Appended to {file_path}"
        else:
            result = "Unknown operation"
    except Exception as exc:
        _log.warning("DB op %s failed: %s", operation, exc)
        result = f"Error: {exc}"

    return create_node_output({"default": result, "topic": result})


@node_handler("notion")
async def execute_notion(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
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
