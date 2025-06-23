"""Node handlers using decorated functions."""

from enum import Enum
from typing import Any, Callable, Dict, Optional

from dipeo_domain.models import DomainNode, NodeExecutionStatus, NodeOutput

from .context import ExecutionContext


class DBOperation(str, Enum):
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
async def execute_start(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    output = create_node_output(
        outputs={'default': ''},
        metadata={"message": "Execution started"}
    )

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output)
    return output


@node_handler("PersonJob")
async def execute_person_job(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    person_id = node.data.get('personId')
    first_only_prompt = node.data.get('firstOnlyPrompt', '')
    default_prompt = node.data.get('defaultPrompt', '')
    max_iteration = node.data.get('maxIteration', 1)

    conversation = ctx.get_conversation_history(person_id) if person_id else []
    exec_count = ctx.exec_counts.get(node.id, 1)

    if not conversation or conversation[0].get("role") != "system":
        person = ctx.diagram.persons.get(person_id, {}) if person_id else {}
        system_prompt = person.get('systemPrompt', '')
        system_msg = {"role": "system", "content": system_prompt}
        conversation.insert(0, system_msg)

    inputs = {}
    for edge in ctx.find_edges_to(node.id):
        source_node_id = edge.source.split(':')[0]
        from_output = ctx.get_node_output(source_node_id)

        edge_label = edge.data.get('label', 'default') if edge.data else 'default'

        if from_output:
            handle_name = edge.target.split(':')[1] if ':' in edge.target else 'default'
            if handle_name == 'first' and exec_count == 1:
                if edge_label in from_output.outputs:
                    inputs[edge_label] = from_output.outputs[edge_label]
            elif handle_name == 'default':
                if 'default' in from_output.outputs:
                    inputs['conversation'] = from_output.outputs['default']

    if exec_count == 1 and first_only_prompt:
        prompt = first_only_prompt
        for key, value in inputs.items():
            prompt = prompt.replace(f'{{{{{key}}}}}', str(value))
    else:
        prompt = default_prompt

    if prompt:
        conversation.append({"role": "user", "content": prompt})

    try:
        person = ctx.diagram.persons.get(person_id, {}) if person_id else {}
        model = person.get('model', 'gpt-4.1-nano')

        response = await ctx.llm_service.call_llm(
            model=model,
            messages=conversation,
            temperature=0.7,
            max_tokens=2000
        )

        ctx.add_to_conversation(person_id, {"role": "assistant", "content": response})

        output = create_node_output(
            outputs={'default': response},
            metadata={"model": model, "tokens_used": len(response.split())}
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
async def execute_endpoint(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    try:
        endpoint_data = node.data.get('data') if node.data else None

        if endpoint_data is not None:
            outputs = {'default': endpoint_data}
        else:
            collected_data = {}
            for edge in ctx.find_edges_to(node.id):
                source_node_id = edge.source.split(':')[0]
                from_output = ctx.get_node_output(source_node_id)

                edge_label = edge.data.get('label', 'default') if edge.data else 'default'

                if from_output and edge_label in from_output.outputs:
                    collected_data[edge_label] = from_output.outputs[edge_label]
            outputs = {'default': collected_data} if collected_data else {}

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
async def execute_condition(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    try:
        input_value = None
        for edge in ctx.find_edges_to(node.id):
            source_node_id = edge.source.split(':')[0]
            from_output = ctx.get_node_output(source_node_id)

            edge_label = edge.data.get('label', 'default') if edge.data else 'default'

            if from_output and edge_label in from_output.outputs:
                input_value = from_output.outputs[edge_label]
                break

        condition_type = node.data.get('conditionType', '') if node.data else ''

        if condition_type == 'detect_max_iterations':
            result = False  # TODO: Implement max iteration detection logic
        else:
            result = False

        outputs = {
            'True' if result else 'False': input_value
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
async def execute_db(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    try:
        input_data = None
        for edge in ctx.find_edges_to(node.id):
            source_node_id = edge.source.split(':')[0]
            from_output = ctx.get_node_output(source_node_id)

            edge_label = edge.data.get('label', 'default') if edge.data else 'default'

            if from_output and edge_label in from_output.outputs:
                input_data = from_output.outputs[edge_label]
                break

        operation = node.data.get('operation', 'read') if node.data else 'read'
        file_path = node.data.get('sourceDetails', '') if node.data else ''

        if operation == "read":
            result = ctx.file_service.read(file_path)
        elif operation == "write":
            await ctx.file_service.write(file_path, str(input_data))
            result = f"Saved to {file_path}"
        elif operation == "append":
            existing_content = ""
            try:
                existing_content = ctx.file_service.read(file_path)
            except:
                pass
            await ctx.file_service.write(file_path, existing_content + str(input_data))
            result = f"Appended to {file_path}"
        else:
            result = "Unknown operation"

        output = create_node_output(
            outputs={'default': result}
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
async def execute_notion(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    try:
        input_data = {}
        for edge in ctx.find_edges_to(node.id):
            source_node_id = edge.source.split(':')[0]
            from_output = ctx.get_node_output(source_node_id)

            edge_label = edge.data.get('label', 'default') if edge.data else 'default'

            if from_output and edge_label in from_output.outputs:
                input_data[edge_label] = from_output.outputs[edge_label]

        action = node.data.get('action', 'read') if node.data else 'read'
        database_id = node.data.get('database_id', '') if node.data else ''

        result = await ctx.notion_service.execute_action(
            action=action,
            database_id=database_id,
            data=input_data
        )

        output = create_node_output(
            outputs={'default': result}
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
