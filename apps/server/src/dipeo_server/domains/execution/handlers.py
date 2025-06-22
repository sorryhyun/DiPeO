"""Node handlers using decorated functions."""

from enum import Enum
from typing import Any, Callable, Dict, Optional

from dipeo_domain.models import (
    NodeType,
    NodeExecutionStatus,
    NodeOutput
)

from .context import ExecutionContext


class DBOperation(str, Enum):
    """Database operation types."""
    LOAD = "LOAD"
    SAVE = "SAVE"
    APPEND = "APPEND"

_handlers: Dict[str, Callable] = {}


def node_handler(node_type: str):
    def decorator(func: Callable):
        _handlers[node_type] = func
        return func
    return decorator


def get_handlers() -> Dict[str, Callable]:
    return _handlers.copy()


def create_node_output(
    outputs: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> NodeOutput:
    return NodeOutput(
        value=outputs,
        metadata=metadata or {}
    )


@node_handler("Start")
async def execute_start(node: NodeType.start, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    output = create_node_output(
        outputs={},
        metadata={"message": "Execution started"}
    )

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output)
    return output


@node_handler("PersonJob")
async def execute_person_job(node: NodeType.person_job, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    conversation = ctx.get_conversation_history(node.person_id) if node.person_id else []

    if not conversation or conversation[0].get("role") != "system":
        system_msg = {"role": "system", "content": node.job}
        conversation.insert(0, system_msg)

    inputs_str = ""
    for edge in ctx.find_edges_to(node.id):
        from_output = ctx.get_node_output(edge.from_node)
        if from_output and edge.label in from_output.outputs:
            inputs_str += f"{edge.label}: {from_output.outputs[edge.label]}\n"

    if inputs_str:
        conversation.append({"role": "user", "content": inputs_str.strip()})

    try:
        response = await ctx.llm_service.call_llm(
            model=node.model,
            messages=conversation,
            temperature=node.temperature,
            max_tokens=node.max_tokens
        )

        ctx.add_to_conversation(node.person_id, {"role": "assistant", "content": response})

        output = create_node_output(
            outputs={node.output: response},
            metadata={"model": node.model, "tokens_used": len(response.split())}
        )

        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output)

        return output

    except Exception as e:
        error_output = create_node_output(
            outputs={},
            metadata={"error": str(e)}
        )
        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.FAILED, error_output)
        return error_output


@node_handler("Endpoint")
async def execute_endpoint(node: NodeType.endpoint, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    try:
        if node.data is not None:
            outputs = {node.output: node.data}
        else:
            collected_data = {}
            for edge in ctx.find_edges_to(node.id):
                from_output = ctx.get_node_output(edge.from_node)
                if from_output and edge.label in from_output.outputs:
                    collected_data[edge.label] = from_output.outputs[edge.label]
            outputs = {node.output: collected_data} if collected_data else {}

        output = create_node_output(
            outputs=outputs
        )

        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output)

        return output

    except Exception as e:
        error_output = create_node_output(
            outputs={},
            metadata={"error": str(e)}
        )
        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.FAILED, error_output)
        return error_output


@node_handler("Condition")
async def execute_condition(node: NodeType.condition, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    try:
        input_value = None
        for edge in ctx.find_edges_to(node.id):
            from_output = ctx.get_node_output(edge.from_node)
            if from_output and edge.label in from_output.outputs:
                input_value = from_output.outputs[edge.label]
                break

        if node.operation == "equals":
            result = str(input_value) == str(node.value)
        elif node.operation == "not_equals":
            result = str(input_value) != str(node.value)
        elif node.operation == "contains":
            result = str(node.value) in str(input_value)
        elif node.operation == "not_contains":
            result = str(node.value) not in str(input_value)
        elif node.operation == "greater_than":
            try:
                result = float(input_value or 0) > float(node.value)
            except (ValueError, TypeError):
                result = False
        elif node.operation == "less_than":
            try:
                result = float(input_value or 0) < float(node.value)
            except (ValueError, TypeError):
                result = False
        else:
            result = False

        outputs = {
            node.true_output if result else node.false_output: input_value
        }

        output = create_node_output(
            outputs=outputs,
            metadata={"condition_result": result}
        )

        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output)

        return output

    except Exception as e:
        error_output = create_node_output(
            outputs={},
            metadata={"error": str(e)}
        )
        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.FAILED, error_output)
        return error_output


@node_handler("DB")
async def execute_db(node: NodeType.db, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    try:
        input_data = None
        for edge in ctx.find_edges_to(node.id):
            from_output = ctx.get_node_output(edge.from_node)
            if from_output and edge.label in from_output.outputs:
                input_data = from_output.outputs[edge.label]
                break

        if node.operation == "LOAD":
            result = ctx.file_service.read(node.file_path)
        elif node.operation == "SAVE":
            await ctx.file_service.write(node.file_path, str(input_data))
            result = f"Saved to {node.file_path}"
        elif node.operation == "APPEND":
            existing_content = ""
            try:
                existing_content = ctx.file_service.read(node.file_path)
            except:
                pass
            await ctx.file_service.write(node.file_path, existing_content + str(input_data))
            result = f"Appended to {node.file_path}"
        else:
            result = "Unknown operation"

        output = create_node_output(
            outputs={node.output: result}
        )

        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output)

        return output

    except Exception as e:
        error_output = create_node_output(
            outputs={},
            metadata={"error": str(e)}
        )
        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.FAILED, error_output)
        return error_output


@node_handler("Notion")
async def execute_notion(node: NodeType.notion, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    try:
        input_data = {}
        for edge in ctx.find_edges_to(node.id):
            from_output = ctx.get_node_output(edge.from_node)
            if from_output and edge.label in from_output.outputs:
                input_data[edge.label] = from_output.outputs[edge.label]

        result = await ctx.notion_service.execute_action(
            action=node.action,
            database_id=node.database_id,
            data=input_data
        )

        output = create_node_output(
            outputs={node.output: result}
        )

        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output)

        return output

    except Exception as e:
        error_output = create_node_output(
            outputs={},
            metadata={"error": str(e)}
        )
        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.FAILED, error_output)
        return error_output
