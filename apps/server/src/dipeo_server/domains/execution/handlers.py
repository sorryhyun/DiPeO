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


def node_handler(node_type: str) -> Callable:
    def decorator(func: Callable) -> Callable:
        _handlers[node_type] = func
        return func
    return decorator


def get_handlers() -> Dict[str, Callable]:
    return _handlers.copy()


def create_node_output(
    value: Dict[str, Any],
    metadata: Optional[Dict[str, Any]] = None,
) -> NodeOutput:
    return NodeOutput(
        value=value,
        metadata=metadata or {}
    )


@node_handler("start")
async def execute_start(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    output = create_node_output(
        value={'default': ''},
        metadata={"message": "Execution started"}
    )

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output)
    return output


@node_handler("person_job")
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
        person_obj = None
        if person_id:
            person_obj = next((p for p in ctx.diagram.persons if p.id == person_id), None)

        system_prompt = (
            getattr(person_obj, 'system_prompt', None)
            or getattr(person_obj, 'systemPrompt', '')
        ) if person_obj else ''
        conversation.insert(0, {"role": "system", "content": system_prompt})

    inputs = {}
    for edge in ctx.find_edges_to(node.id):
        source_node_id = edge.source.split(':')[0]
        from_output = ctx.get_node_output(source_node_id)

        edge_label = edge.data.get('label', 'default') if edge.data else 'default'

        if from_output:
            handle_name = edge.target.split(':')[1] if ':' in edge.target else 'default'
            if handle_name == 'first' and exec_count == 1:
                if edge_label in from_output.value:
                    inputs[edge_label] = from_output.value[edge_label]
            elif handle_name == 'default':
                if 'default' in from_output.value:
                    inputs['conversation'] = from_output.value['default']

    if exec_count == 1 and first_only_prompt:
        prompt = first_only_prompt
        for key, value in inputs.items():
            prompt = prompt.replace(f'{{{{{key}}}}}', str(value))
    else:
        prompt = default_prompt

    if prompt:
        conversation.append({"role": "user", "content": prompt})

    try:
        # ctx.diagram.persons is a list, not a dict
        person_obj = None
        if person_id:
            person_obj = next((p for p in ctx.diagram.persons if p.id == person_id), None)

        # Use a fallback dict to avoid repetitive attribute checks
        person = {
            'service': getattr(person_obj, 'service', 'openai'),
            'api_key_id': getattr(person_obj, 'api_key_id', None) or getattr(person_obj, 'apiKeyId', None),
            'model': getattr(person_obj, 'model', 'gpt-4.1-nano'),
        }

        service = person['service']
        api_key_id = person['api_key_id']
        model = person['model']

        # Call the LLM service with the updated signature
        llm_result = await ctx.llm_service.call_llm(
            service=service,
            api_key_id=api_key_id,
            model=model,
            messages=conversation,
        )

        # Extract response text and token usage from returned dict
        response_text = llm_result.get("response", "")
        token_usage = llm_result.get("token_usage")

        ctx.add_to_conversation(person_id, {"role": "assistant", "content": response_text})

        if token_usage is None:
            # Fallback to naive word count if the adapter didn't return usage
            token_usage = len(str(response_text).split())

        output = create_node_output(
            value={'default': response_text},
            metadata={"model": model, "tokens_used": token_usage}
        )

        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output)

        return output

    except Exception as e:
        error_output = create_node_output(
            value={},
            metadata={"error": str(e)}
        )
        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.FAILED, error_output)
        return error_output


@node_handler("endpoint")
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

                if from_output and edge_label in from_output.value:
                    collected_data[edge_label] = from_output.value[edge_label]
            outputs = {'default': collected_data} if collected_data else {}

        output = create_node_output(
            value=outputs
        )

        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output)

        return output

    except Exception as e:
        error_output = create_node_output(
            value={},
            metadata={"error": str(e)}
        )
        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.FAILED, error_output)
        return error_output


@node_handler("condition")
async def execute_condition(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    try:
        input_value = None
        for edge in ctx.find_edges_to(node.id):
            source_node_id = edge.source.split(':')[0]
            from_output = ctx.get_node_output(source_node_id)

            edge_label = edge.data.get('label', 'default') if edge.data else 'default'

            if from_output and edge_label in from_output.value:
                input_value = from_output.value[edge_label]
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
            value=outputs,
            metadata={"condition_result": result}
        )

        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output)

        return output

    except Exception as e:
        error_output = create_node_output(
            value={},
            metadata={"error": str(e)}
        )
        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.FAILED, error_output)
        return error_output


@node_handler("db")
async def execute_db(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    import logging
    log = logging.getLogger(__name__)
    
    log.info(f"Executing DB node {node.id}")
    ctx.increment_exec_count(node.id)

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    try:
        input_data = None
        for edge in ctx.find_edges_to(node.id):
            source_node_id = edge.source.split(':')[0]
            from_output = ctx.get_node_output(source_node_id)

            edge_label = edge.data.get('label', 'default') if edge.data else 'default'

            if from_output and edge_label in from_output.value:
                input_data = from_output.value[edge_label]
                break

        operation = node.data.get('operation', 'read') if node.data else 'read'
        file_path = node.data.get('sourceDetails', '') if node.data else ''

        if operation == "read":
            try:
                result = ctx.file_service.read(file_path)
            except Exception as e:
                result = f"Error reading file: {str(e)}"
                log.warning(f"Error reading file {file_path}: {e}")
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

        # Always expose the primary result both as "default" and "topic" so that
        # downstream edges that are labelled "topic" (a common pattern for file
        # loading scenarios) can resolve the input without having to duplicate
        # the data at the arrow level.
        output = create_node_output(value={
            'default': result,
            'topic': result,
        })
        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output)

        return output

    except Exception as e:
        log.error(f"DB node {node.id} failed with error: {e}", exc_info=True)
        error_output = create_node_output(
            value={
                'default': f"Error: {str(e)}",
                'topic': f"Error: {str(e)}",
            },
            metadata={"error": str(e)}
        )
        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, error_output)  # Mark as completed, not failed
        return error_output


@node_handler("notion")
async def execute_notion(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    ctx.increment_exec_count(node.id)

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    try:
        input_data = {}
        for edge in ctx.find_edges_to(node.id):
            source_node_id = edge.source.split(':')[0]
            from_output = ctx.get_node_output(source_node_id)

            edge_label = edge.data.get('label', 'default') if edge.data else 'default'

            if from_output and edge_label in from_output.value:
                input_data[edge_label] = from_output.value[edge_label]

        action = node.data.get('action', 'read') if node.data else 'read'
        database_id = node.data.get('database_id', '') if node.data else ''

        result = await ctx.notion_service.execute_action(
            action=action,
            database_id=database_id,
            data=input_data
        )

        output = create_node_output(
            value={'default': result}
        )

        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output)

        return output

    except Exception as e:
        error_output = create_node_output(
            value={},
            metadata={"error": str(e)}
        )
        await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.FAILED, error_output)
        return error_output
