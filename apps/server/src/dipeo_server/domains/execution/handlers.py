from __future__ import annotations

import logging
from enum import Enum
from typing import TYPE_CHECKING, Any, Awaitable, Callable, Dict, Optional

from dipeo_domain.models import DomainNode, NodeExecutionStatus, NodeOutput

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

    async def _wrapped(node: DomainNode, ctx: ExecutionContext, **kwargs: Any) -> NodeOutput:  # type: ignore[override]
        await ctx.state_store.update_node_status(
            ctx.execution_id, node.id, NodeExecutionStatus.RUNNING
        )
        try:
            output = await func(node, ctx, **kwargs)
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
    node_view: Optional[Any] = None,
) -> Dict[str, Any]:
    """Collect downstream values from all incoming edges.

    Returned mapping keys are the *edge labels* (defaulting to "default").
    If *as_dict* is False, only the first matching payload is returned.
    """
    
    # If we have a node_view, use its condition-aware getter
    if node_view is not None and hasattr(node_view, 'get_active_inputs'):
        results = node_view.get_active_inputs()
        if not as_dict and results:
            return next(iter(results.values()), None)
        return results
    
    # Fallback to legacy behavior if no node_view
    # This path should be removed once all handlers are updated
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


@node_handler("start")
async def execute_start(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    """Kick‑off node: no input, always succeeds."""
    return create_node_output({"default": ""}, {"message": "Execution started"})


@node_handler("person_job")
async def execute_person_job(
    node: DomainNode, 
    ctx: ExecutionContext,
    node_view: Optional["NodeView"] = None
) -> NodeOutput:
    """Handle conversational *person_job* node using domain services."""
    exec_count = ctx.exec_counts.get(node.id, 0)
    data = node.data or {}
    
    # Extract node configuration
    person_id: Optional[str] = data.get("personId") or data.get("person")
    first_only_prompt: str = data.get("firstOnlyPrompt", "")
    default_prompt: str = data.get("defaultPrompt", "")
    forgetting_mode: Optional[str] = data.get("forgettingMode")
    is_judge: bool = "judge" in data.get("label", "").lower()
    
    if not person_id:
        return create_node_output({}, {"error": "No personId specified"})
    
    # Get person configuration
    person_obj = ctx.conversation_service.find_person_by_id(ctx.diagram.persons, person_id)
    person_config = ctx.conversation_service.get_person_config(person_obj)
    
    # Handle forgetting mode
    if forgetting_mode == "on_every_turn" and exec_count > 1:
        # Forget messages from previous turns
        ctx.conversation_service.forget_own_messages_for_person(
            person_id, ctx.execution_id
        )
    
    # Get conversation history from memory service
    conversation = ctx.conversation_service.get_conversation_for_person(
        person_id, ctx.execution_id
    )

    # Collect inputs from edges
    inputs = await _edge_inputs(node, ctx, node_view=node_view)
    
    # Handle conversation inputs (multi-person conversation loops)
    if "conversation" in inputs:
        upstream_conv = inputs["conversation"]
        if isinstance(upstream_conv, list) and upstream_conv:
            # Check if we're in a conversation loop
            our_messages_count = sum(
                1 for msg in upstream_conv
                if msg.get("personId") == person_id and msg.get("role") == "assistant"
            )
            
            if our_messages_count > 0:
                # In a loop - extract last exchange from other persons
                last_other_msg = None
                for i in range(len(upstream_conv) - 1, -1, -1):
                    msg = upstream_conv[i]
                    if msg.get("personId") != person_id and msg.get("role") == "assistant":
                        last_other_msg = msg
                        break
                
                if last_other_msg:
                    # Add as a message to memory service
                    await ctx.conversation_service.add_message_to_conversation(
                        sender_person_id=last_other_msg.get('personId', 'unknown'),
                        participant_person_ids=[person_id],
                        content=last_other_msg.get('content', ''),
                        execution_id=ctx.execution_id,
                        node_id=node.id,
                        node_label=data.get('label', node.id)
                    )
            else:
                # Not in a loop - format upstream conversation as context
                last_exchange = []
                for msg in reversed(upstream_conv):
                    if msg.get("role") in ["user", "assistant"]:
                        last_exchange.append(msg)
                        if len(last_exchange) == 2:
                            break
                
                if last_exchange:
                    context_parts = []
                    for msg in reversed(last_exchange):
                        role = "Input" if msg.get("role") == "user" else "Response"
                        context_parts.append(f"{role}: {msg.get('content', '')}")
                    
                    upstream_text = "\n".join(context_parts)
                    # Add as a user message
                    await ctx.conversation_service.add_message_to_conversation(
                        sender_person_id="user",
                        participant_person_ids=[person_id],
                        content=upstream_text,
                        execution_id=ctx.execution_id,
                        node_id=node.id,
                        node_label=data.get('label', node.id)
                    )

    # Prepare prompt
    prompt = ctx.conversation_service.prepare_prompt(
        exec_count, first_only_prompt, default_prompt, inputs
    )
    
    # Handle judge aggregation
    if is_judge:
        debate_context_parts = []
        for other_node in ctx.diagram.nodes:
            if other_node.type != "person_job" or other_node.id == node.id:
                continue
            
            other_person_id = other_node.data.get("personId") if other_node.data else None
            if not other_person_id:
                continue
            
            # Get conversation for the other person
            other_conv = ctx.conversation_service.get_conversation_for_agent(
                other_person_id, ctx.execution_id
            )
            
            # Filter out system messages
            debate_messages = [m for m in other_conv if m.get("role") != "system"]
            if not debate_messages:
                continue
            
            label = other_node.data.get("label", other_node.id) if other_node.data else other_node.id
            debate_context_parts.append(f"\n{label}:\n")
            
            for msg in debate_messages:
                role = "Input" if msg.get("role") == "user" else "Response"
                content = msg.get("content", "")
                debate_context_parts.append(f"{role}: {content}\n")
        
        if debate_context_parts:
            debate_txt = (
                "Here are the arguments from different panels:\n"
                + "".join(debate_context_parts)
                + "\n\n"
            )
            prompt = debate_txt + (
                prompt or "Based on the above arguments, judge which panel is more reasonable."
            )
    
    # Add prompt as user message if present
    if prompt:
        await ctx.conversation_service.add_message_to_conversation(
            sender_agent_id="user",
            participant_agent_ids=[person_id],
            content=prompt,
            execution_id=ctx.execution_id,
            node_id=node.id,
            node_label=data.get('label', node.id)
        )

    # Get updated conversation from memory service
    conversation = ctx.conversation_service.get_conversation_for_person(
        person_id, ctx.execution_id
    )
    
    # Call LLM with conversation
    llm_result = await ctx.llm_service.call_llm(
        service=person_config["service"],
        api_key_id=person_config["api_key_id"],
        model=person_config["model"],
        messages=conversation,
    )

    response_text: str = llm_result.get("response", "")
    token_usage_obj = llm_result.get("token_usage")
    
    # Add response to memory
    message = await ctx.conversation_service.add_message_to_conversation(
        sender_person_id=person_id,
        participant_person_ids=[person_id],
        content=response_text,
        execution_id=ctx.execution_id,
        node_id=node.id,
        node_label=data.get('label', node.id),
        input_tokens=getattr(token_usage_obj, "input", 0) if token_usage_obj else 0,
        output_tokens=getattr(token_usage_obj, "output", 0) if token_usage_obj else 0,
        cached_tokens=getattr(token_usage_obj, "cached", 0) if token_usage_obj and hasattr(token_usage_obj, "cached") else 0
    )

    # Prepare output values
    output_values = {"default": response_text}
    
    # Check if we need to output conversation state
    for edge in ctx.diagram.arrows:
        if edge.source.startswith(node.id + ":"):
            edge_data = edge.data if edge.data and isinstance(edge.data, dict) else {}
            if edge_data.get("contentType") == "conversation_state":
                # Get full conversation history for output
                conv_history = ctx.conversation_service.get_conversation_for_agent(
                    person_id, ctx.execution_id
                )
                output_values["conversation"] = conv_history
                break

    # Prepare token usage metadata
    token_usage_metadata = {}
    if token_usage_obj and hasattr(token_usage_obj, "__dict__"):
        token_usage_metadata = {
            "input": getattr(token_usage_obj, "input", 0),
            "output": getattr(token_usage_obj, "output", 0),
            "total": getattr(token_usage_obj, "total", 0),
        }
        if hasattr(token_usage_obj, "cached"):
            token_usage_metadata["cached"] = token_usage_obj.cached
        
        # Accumulate token usage in context
        from dipeo_domain import TokenUsage as DomainTokenUsage
        ctx.add_token_usage(
            node.id, 
            DomainTokenUsage(**token_usage_metadata)
        )
    
    return create_node_output(
        output_values,
        {
            "model": person_config["model"],
            "tokens_used": token_usage_metadata.get("total", 0),
            "tokenUsage": token_usage_metadata
        },
    )


@node_handler("endpoint")
async def execute_endpoint(
    node: DomainNode, 
    ctx: ExecutionContext,
    node_view: Optional["NodeView"] = None
) -> NodeOutput:
    """Endpoint node – pass through data and optionally save to file."""

    data = node.data or {}

    if (direct := data.get("data")) is not None:
        result_data = direct
    else:
        collected = await _edge_inputs(node, ctx, node_view=node_view)
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
async def execute_condition(
    node: DomainNode, 
    ctx: ExecutionContext,
    node_view: Optional["NodeView"] = None
) -> NodeOutput:
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
    inputs = await _edge_inputs(node, ctx, as_dict=True, node_view=node_view)

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
async def execute_db(
    node: DomainNode, 
    ctx: ExecutionContext,
    node_view: Optional["NodeView"] = None
) -> NodeOutput:
    """File‑based DB node supporting *read*, *write* and *append* operations."""

    data = node.data or {}
    operation = data.get("operation", "read")
    file_path = data.get("sourceDetails", "")

    input_val = await _edge_inputs(node, ctx, as_dict=False, node_view=node_view)

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
async def execute_notion(
    node: DomainNode, 
    ctx: ExecutionContext,
    node_view: Optional["NodeView"] = None
) -> NodeOutput:
    """Wrapper around `ctx.notion_service.execute_action`."""

    data = node.data or {}
    action = data.get("action", "read")
    database_id = data.get("database_id", "")
    payload = await _edge_inputs(node, ctx, node_view=node_view)

    result = await ctx.notion_service.execute_action(
        action=action,
        database_id=database_id,
        data=payload,
    )
    return create_node_output({"default": result})
