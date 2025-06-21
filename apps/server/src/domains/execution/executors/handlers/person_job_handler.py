"""
Handler for PersonJob nodes - LLM tasks with memory management
"""

from typing import Dict, Any, List
import time
import logging

from ..schemas.person_job import PersonJobProps, PersonBatchJobProps
from ..types import ExecutionContext
from src.__generated__.models import NodeOutput
from src.domains.llm.services.token_usage_service import TokenUsageService
from src.common.processors import OutputProcessor
from ..decorators import node

logger = logging.getLogger(__name__)


@node(
    node_type="person_job",
    schema=PersonJobProps,
    description="Execute LLM task with person context and memory",
    requires_services=["llm_service", "memory_service", "interactive_handler"]
)
async def person_job_handler(
    props: PersonJobProps,
    context: ExecutionContext,
    inputs: Dict[str, Any],
    services: Dict[str, Any]
) -> Any:
    """Handle PersonJob execution with LLM"""
    
    start_time = time.time()
    node_id = context.current_node_id
    execution_count = context.exec_cnt.get(node_id, 0)
    
    # Check execution limit
    if props.maxIteration and execution_count >= props.maxIteration:
        last_output = context.outputs.get(node_id, "No previous output")
        return NodeOutput(
            value=last_output,
            metadata={
                "skipped": True,
                "reason": f"Max iterations ({props.maxIteration}) reached",
                "executionCount": execution_count,
                "passthrough": True,
                "tokenUsage": TokenUsageService.zero().model_dump(),
                "executionTime": time.time() - start_time
            }
        )
    
    # Get the appropriate prompt
    prompt = props.get_effective_prompt(execution_count)
    if not prompt:
        return NodeOutput(
            value=None,
            metadata={
                "error": "No prompt available",
                "executionCount": execution_count,
                "tokenUsage": TokenUsageService.zero().model_dump(),
                "executionTime": time.time() - start_time
            }
        )
    
    # Resolve person configuration
    person = await _resolve_person(props, context)
    
    # Get input values with appropriate handle filter
    # For new unified executor, inputs are already provided
    # But we need to handle conversation_state inputs specially
    conversation_inputs = await _get_conversation_inputs(context, node_id)
    
    # Substitute variables in prompt
    final_prompt = props.substitute_variables(prompt, inputs)
    
    # Get services
    llm_service = services.get("llm_service")
    memory_service = services.get("memory_service")
    interactive_handler = services.get("interactive_handler")
    
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
    if props.interactive and interactive_handler:
        interactive_response = await interactive_handler(
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
        
        response = await llm_service.call_llm(
            service=service,
            api_key_id=person.api_key_id,
            model=person.model,
            messages=messages,
            system_prompt=person.systemPrompt or ""
        )
        
        elapsed = time.time() - start_time
        usage = TokenUsageService.from_response(response)
        
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
        
        # Return unified NodeOutput format
        return NodeOutput(
            value=response["response"],
            metadata={
                "tokenUsage": usage.model_dump() if usage else None,
                "executionTime": elapsed,
                "conversationHistory": messages[:-1],
                "model": person.model,
                "service": service
            }
        )
        
    except Exception as e:
        logger.error(f"LLM call failed for node {node_id}: {str(e)}")
        raise


@node(
    node_type="person_batch_job",
    schema=PersonBatchJobProps,
    description="Execute LLM task in batch mode",
    requires_services=["llm_service", "memory_service", "interactive_handler"]
)
async def person_batch_job_handler(
    props: PersonBatchJobProps,
    context: ExecutionContext,
    inputs: Dict[str, Any],
    services: Dict[str, Any]
) -> Any:
    """Handle PersonBatchJob execution"""
    
    # Use the regular person job handler
    result = await person_job_handler(props, context, inputs, services)
    
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
        from src.common.utils.app_context import app_context
        api_key_info = app_context.api_key_service.get_api_key(api_key_id)
        return api_key_info.get("service", "openai")
    except Exception as e:
        logger.warning(f"Failed to get API key info for {api_key_id}: {e}")
        return "openai"  # Default service


async def _get_conversation_inputs(context: ExecutionContext, node_id: str) -> List[Dict[str, str]]:
    """Extract conversation history from incoming connections"""
    conversation_inputs = []
    
    # Check incoming connections for conversation_state handle
    # In the new architecture, graph is not part of context
    # Instead, we should use the edges information
    for edge in context.edges:
        if edge["target"] == node_id and edge.get("targetHandle") == "conversation_state":
            source_node_id = edge["source"]
            output = context.outputs.get(source_node_id)
            if OutputProcessor.is_personjob_output(output):
                conv_history = OutputProcessor.extract_conversation_history(output) or []
                conversation_inputs.extend(conv_history)
                
                # Also add the actual output as user input
                value = OutputProcessor.extract_value(output)
                if value:
                    conversation_inputs.append({"role": "user", "content": value})
    
    return conversation_inputs