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
    # Engine already manages exec_count

    output = create_node_output(
        value={'default': ''},
        metadata={"message": "Execution started"}
    )

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.COMPLETED, output)
    return output


@node_handler("person_job")
async def execute_person_job(node: DomainNode, ctx: ExecutionContext) -> NodeOutput:
    import logging
    log = logging.getLogger(__name__)
    
    log.info(f"=== PERSON_JOB HANDLER CALLED for node {node.id} ===")
    # Don't increment here - the engine already incremented it
    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    person_id = node.data.get('personId')
    first_only_prompt = node.data.get('firstOnlyPrompt', '')
    default_prompt = node.data.get('defaultPrompt', '')
    max_iteration = node.data.get('maxIteration', 1)

    # Check if this is a judge node that needs to see other conversations
    is_judge = 'judge' in node.data.get('label', '').lower() if node.data else False
    
    conversation = ctx.get_conversation_history(person_id) if person_id else []
    exec_count = ctx.exec_counts.get(node.id, 0)
    
    forgetting_mode = node.data.get('forgettingMode') if node.data else None
    
    if forgetting_mode == 'on_every_turn' and exec_count > 1:
        conversation = [msg for msg in conversation if msg.get('role') in ['system', 'user']]

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
        handle_name = edge.target.split(':')[1] if ':' in edge.target else 'default'
        

        if from_output:
            if handle_name == 'first' and exec_count == 1:
                if edge_label in from_output.value:
                    inputs[edge_label] = from_output.value[edge_label]
                else:
                    log.warning(f"Edge label '{edge_label}' not found in source output keys: {list(from_output.value.keys())}")
            elif handle_name == 'default':
                if 'default' in from_output.value:
                    inputs['conversation'] = from_output.value['default']
                else:
                    log.warning(f"'default' key not found in source output keys: {list(from_output.value.keys())}")
        else:
            log.warning(f"No output found for source node {source_node_id}!")

    if 'conversation' in inputs and exec_count > 1:
        conversation.append({"role": "user", "content": inputs['conversation']})

    if exec_count == 1 and first_only_prompt:
        prompt = first_only_prompt
        for key, value in inputs.items():
            prompt = prompt.replace(f'{{{{{key}}}}}', str(value))
    else:
        prompt = default_prompt

    # If this is a judge node, collect conversations from other person_job nodes
    if is_judge:
        # Find all person_job nodes that have executed
        debate_context = []
        for other_node in ctx.diagram.nodes:
            if other_node.type == 'person_job' and other_node.id != node.id:
                other_person_id = other_node.data.get('personId') if other_node.data else None
                if other_person_id:
                    other_conversation = ctx.get_conversation_history(other_person_id)
                    if other_conversation:
                        # Extract the actual debate content (skip system prompts)
                        panel_label = other_node.data.get('label', other_node.id) if other_node.data else other_node.id
                        debate_messages = [msg for msg in other_conversation if msg.get('role') != 'system']
                        if debate_messages:
                            debate_context.append(f"\n{panel_label}:\n")
                            for msg in debate_messages:
                                role = msg.get('role', 'unknown')
                                content = msg.get('content', '')
                                if role == 'user':
                                    debate_context.append(f"Input: {content}\n")
                                elif role == 'assistant':
                                    debate_context.append(f"Response: {content}\n")
        
        if debate_context:
            # Prepend the debate context to the judge's prompt
            full_context = "Here are the arguments from different panels:\n" + "".join(debate_context) + "\n\n"
            if prompt:
                prompt = full_context + prompt
            else:
                prompt = full_context + "Based on the above arguments, judge which panel is more reasonable."
    
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
    # Engine already manages exec_count

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

                if from_output:
                    if edge_label in from_output.value:
                        collected_data[edge_label] = from_output.value[edge_label]
                    else:
                        import logging
                        log = logging.getLogger(__name__)
                        log.warning(f"Edge label '{edge_label}' not found in source output from {source_node_id}")
                else:
                    import logging
                    log = logging.getLogger(__name__)
                    log.warning(f"No output found for source node {source_node_id} when collecting data for endpoint")
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
    # Engine already manages exec_count

    await ctx.state_store.update_node_status(ctx.execution_id, node.id, NodeExecutionStatus.RUNNING)

    try:
        # For condition nodes, we just need to check the condition, not collect data
        input_value = None
        for edge in ctx.find_edges_to(node.id):
            source_node_id = edge.source.split(':')[0]
            from_output = ctx.get_node_output(source_node_id)

            edge_label = edge.data.get('label', 'default') if edge.data else 'default'

            if from_output:
                if edge_label in from_output.value:
                    input_value = from_output.value[edge_label]
                else:
                    log.warning(f"Edge label '{edge_label}' not found in source output from {source_node_id} for condition node")
            else:
                log.warning(f"No output found for source node {source_node_id} when evaluating condition")
                break

        condition_type = node.data.get('conditionType', '') if node.data else ''

        if condition_type == 'detect_max_iterations':
            # Check execution counts of all incoming nodes
            # Result should be True only if ALL person_job nodes have reached their max iterations
            result = True
            for edge in ctx.find_edges_to(node.id):
                source_node_id = edge.source.split(':')[0]
                source_node = next((n for n in ctx.diagram.nodes if n.id == source_node_id), None)
                
                if source_node and source_node.type == 'person_job':
                    exec_count = ctx.exec_counts.get(source_node_id, 0)
                    max_iteration = source_node.data.get('maxIteration', 1) if source_node.data else 1
                    
                    if exec_count < max_iteration:
                        result = False
                        break
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
    # Engine already manages exec_count

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
                # Check if aread exists, otherwise fall back to sync read
                if hasattr(ctx.file_service, 'aread'):
                    result = await ctx.file_service.aread(file_path)
                else:
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
                existing_content = await ctx.file_service.aread(file_path)
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
    # Engine already manages exec_count

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
