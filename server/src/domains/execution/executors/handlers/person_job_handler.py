"""
Handler for PersonJob nodes - LLM tasks with memory management
"""

from typing import Dict, Any, List, Optional
import time
import logging

from ..schemas.person_job import PersonJobProps, PersonBatchJobProps
from ..types import ExecutionContext, ExecutorResult
from ....diagram.models.domain import TokenUsage
from src.shared.utils.output_processor import OutputProcessor
from src.shared.utils.app_context import get_memory_service
from ..executor_utils import get_input_values, substitute_variables

logger = logging.getLogger(__name__)


async def person_job_handler(
    props: PersonJobProps,
    context: ExecutionContext,
    inputs: Dict[str, Any]
) -> Any:
    """Handle PersonJob execution with LLM"""
    
    start_time = time.time()
    node_id = context.current_node_id
    execution_count = context.exec_cnt.get(node_id, 0)
    
    # Check execution limit
    if props.maxIteration and execution_count >= props.maxIteration:
        last_output = context.outputs.get(node_id, "No previous output")
        return {
            "output": last_output,
            "metadata": {
                "skipped": True,
                "reason": f"Max iterations ({props.maxIteration}) reached",
                "execution_count": execution_count,
                "passthrough": True
            },
            "tokens": TokenUsage(),
            "execution_time": time.time() - start_time
        }
    
    # Get the appropriate prompt
    prompt = props.get_effective_prompt(execution_count)
    if not prompt:
        return {
            "output": None,
            "error": "No prompt available",
            "metadata": {"execution_count": execution_count},
            "tokens": TokenUsage(),
            "execution_time": time.time() - start_time
        }
    
    # Resolve person configuration
    person = await _resolve_person(props, context)
    
    # Get input values with appropriate handle filter
    handler = "first" if execution_count == 0 else "default"
    # For new unified executor, inputs are already provided
    # But we need to handle conversation_state inputs specially
    conversation_inputs = await _get_conversation_inputs(context, node_id)
    
    # Substitute variables in prompt
    final_prompt = props.substitute_variables(prompt, inputs)
    
    # Handle memory cleanup
    try:
        memory_service = get_memory_service()
    except RuntimeError:
        # Memory service not available (e.g., in tests)
        memory_service = None
    
    person_id = person.id or node_id
    
    if memory_service and props.contextCleaningRule != "no_forget":
        if props.contextCleaningRule == "on_every_turn":
            memory_service.forget_for_person(person_id)
        else:
            memory_service.forget_own_messages_for_person(
                person_id, 
                getattr(context, 'execution_id', None)
            )
    
    # Build message history
    history = memory_service.get_conversation_history(person_id) if memory_service else []
    messages = history + conversation_inputs + [{"role": "user", "content": final_prompt}]
    
    # Handle interactive mode
    if props.interactive and hasattr(context, 'interactive_handler'):
        interactive_response = await context.interactive_handler(
            node_id=node_id,
            prompt=final_prompt,
            context={
                "person_id": person_id,
                "person_name": props.label or person.name or "Person",
                "model": person.model,
                "service": person.service,
                "execution_count": execution_count
            }
        )
        if interactive_response:
            messages.append({"role": "user", "content": interactive_response})
            final_prompt += f"\n\nUser response: {interactive_response}"
    
    # Call LLM service
    try:
        logger.debug(f"PersonJob {node_id} execution #{execution_count}")
        
        # Get service from API key if not specified
        service = person.service or await _get_service_from_api_key(person.api_key_id, context)
        
        response = await context.llm_service.call_llm(
            service=service,
            api_key_id=person.api_key_id,
            model=person.model,
            messages=messages,
            system_prompt=person.systemPrompt or ""
        )
        
        elapsed = time.time() - start_time
        usage = TokenUsage.from_response(response)
        
        # Store in memory
        if memory_service and hasattr(context, 'execution_id'):
            memory_service.add_message_to_conversation(
                content=final_prompt,
                sender_person_id="user",
                execution_id=context.execution_id,
                participant_person_ids=[person_id],
                role="user",
                node_id=node_id,
                node_label=props.label or "PersonJob"
            )
            
            memory_service.add_message_to_conversation(
                content=response["response"],
                sender_person_id=person_id,
                execution_id=context.execution_id,
                participant_person_ids=[person_id],
                role="assistant",
                node_id=node_id,
                node_label=props.label or "PersonJob",
                token_count=usage.total,
                input_tokens=usage.input,
                output_tokens=usage.output,
                cached_tokens=usage.cached
            )
        
        # Update execution count
        context.exec_cnt[node_id] = execution_count + 1
        
        # Build output using OutputProcessor
        output = OutputProcessor.create_personjob_output_from_tokens(
            text=response["response"],
            token_usage=usage,
            conversation_history=messages[:-1],
            model=person.model,
            execution_time=elapsed
        )
        
        return output
        
    except Exception as e:
        logger.error(f"LLM call failed for node {node_id}: {str(e)}")
        raise


async def person_batch_job_handler(
    props: PersonBatchJobProps,
    context: ExecutionContext,
    inputs: Dict[str, Any]
) -> Any:
    """Handle PersonBatchJob execution"""
    
    # Use the regular person job handler
    result = await person_job_handler(props, context, inputs)
    
    # Add batch-specific metadata if result is a dict
    if isinstance(result, dict) and 'metadata' in result:
        result['metadata'].update({
            "node_type": "person_batch_job",
            "batch_size": props.batchSize,
            "is_batch": True
        })
    
    return result


async def _resolve_person(props: PersonJobProps, context: ExecutionContext) -> Any:
    """Resolve person from ID or inline config"""
    if props.person:
        # Use inline person config
        return props.person
    
    # Fetch existing person from context
    persons = getattr(context, 'persons', {})
    person = persons.get(props.personId)
    
    if not person:
        raise ValueError(f"Person not found: {props.personId}")
    
    # Convert to PersonConfig-like object if needed
    from ..schemas.person_job import PersonConfig
    if isinstance(person, dict):
        return PersonConfig(**person)
    
    return person


async def _get_service_from_api_key(api_key_id: str, context: ExecutionContext) -> str:
    """Get service type from API key"""
    try:
        from src.shared.utils.app_context import app_context
        api_key_info = app_context.api_key_service.get_api_key(api_key_id)
        return api_key_info.get("service", "openai")
    except Exception as e:
        logger.warning(f"Failed to get API key info for {api_key_id}: {e}")
        return "openai"  # Default service


async def _get_conversation_inputs(context: ExecutionContext, node_id: str) -> List[Dict[str, str]]:
    """Extract conversation history from incoming connections"""
    conversation_inputs = []
    
    # Check incoming connections for conversation_state handle
    for arrow in context.graph.incoming.get(node_id, []):
        if arrow.label == "conversation_state" or arrow.t_handle == "conversation_state":
            output = context.outputs.get(arrow.source)
            if OutputProcessor.is_personjob_output(output):
                conv_history = OutputProcessor.extract_conversation_history(output) or []
                conversation_inputs.extend(conv_history)
                
                # Also add the actual output as user input
                value = OutputProcessor.extract_value(output)
                if value:
                    conversation_inputs.append({"role": "user", "content": value})
    
    return conversation_inputs