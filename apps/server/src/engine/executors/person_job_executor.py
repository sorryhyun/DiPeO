"""
PersonJob node executor - handles LLM API calls with person configuration
"""

from typing import Dict, Any, TYPE_CHECKING
import time
import logging

if TYPE_CHECKING:
    from ..engine import ExecutionContext

from .base_executor import BaseExecutor, ExecutorResult
from .utils import (
    get_input_values,
    substitute_variables
)
from .token_utils import TokenUsage
from .validator import (
    ValidationResult,
    validate_required_fields,
    validate_positive_integer,
    validate_either_required,
    validate_enum_field
)
from ...services.llm_service import LLMService

logger = logging.getLogger(__name__)


class PersonJobExecutor(BaseExecutor):
    """
    PersonJob node executor that makes LLM calls with person configuration.
    This executor handles stateful conversations with memory management.
    """
    
    def __init__(self, llm_service: LLMService):
        super().__init__()
        self.llm_service = llm_service
    
    async def validate(self, node: Dict[str, Any], context: 'ExecutionContext') -> ValidationResult:
        """Validate PersonJob node configuration"""
        errors = []
        warnings = []
        
        properties = node.get("properties", {})
        
        # Check for person configuration - either embedded or via personId
        person_config = properties.get("person", {})
        person_id = properties.get("personId")
        
        if not person_config and person_id:
            # Look up person from context
            person = context.persons.get(person_id)
            if person:
                person_config = person
            else:
                errors.append(f"Person with ID '{person_id}' not found in diagram")
        
        # Validate either person or personId is provided
        either_errors = validate_either_required(
            properties,
            [["person", "personId"]],
            ["Either person configuration or personId is required"]
        )
        errors.extend(either_errors)
        
        if person_config:
            # Validate required person fields
            person_field_errors = validate_required_fields(
                person_config,
                ["apiKeyId"],
                {"apiKeyId": "API key ID"}
            )
            errors.extend(person_field_errors)
            
            # Validate model field (could be modelName or model)
            if not person_config.get("modelName") and not person_config.get("model"):
                errors.append("Model name is required in person configuration")
            
            # Validate service enum
            service_error = validate_enum_field(
                person_config,
                "service",
                ["openai", "claude", "gemini", "grok"],
                case_sensitive=True
            )
            if service_error:
                warnings.append(service_error.replace("Invalid", "Unsupported"))
        
        # Validate prompts - either prompt or defaultPrompt required
        prompt_errors = validate_either_required(
            properties,
            [["prompt", "defaultPrompt"]],
            ["Either prompt or defaultPrompt is required"]
        )
        errors.extend(prompt_errors)
        
        # Validate maxIteration using centralized validation
        iteration_error = validate_positive_integer(
            properties,
            "maxIteration",
            min_value=1,
            required=False
        )
        if iteration_error:
            errors.append(iteration_error)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def execute(self, node: Dict[str, Any], context: 'ExecutionContext') -> ExecutorResult:
        """Execute PersonJob node - make LLM call with person configuration"""
        start_time = time.time()
        
        properties = node.get("properties", {})
        person_config = properties.get("person", {})
        person_id = properties.get("personId")
        node_id = node.get("id", "")
        
        # Get person configuration - either embedded or via personId
        if not person_config and person_id:
            person_config = context.persons.get(person_id, {})
        
        # Get input values for variable substitution
        inputs = get_input_values(node, context)
        
        # Check iteration count and handle first-only logic
        execution_count = context.node_execution_counts.get(node_id, 0)
        max_iterations = properties.get("maxIteration")
        
        # Skip if max iterations reached
        if max_iterations and execution_count >= max_iterations:
            logger.debug(f"PersonJob {node_id} skipping: execution_count={execution_count} >= max_iterations={max_iterations}")
            # Get the last output from context to pass through
            last_output = context.node_outputs.get(node_id, "No previous output")
            return ExecutorResult(
                output=last_output,  # Pass through last output so downstream nodes can use it
                metadata={
                    "skipped": True,
                    "reason": f"Max iterations ({max_iterations}) reached",
                    "execution_count": execution_count,
                    "passthrough": True
                },
                tokens=TokenUsage(),
                execution_time=time.time() - start_time
            )
        
        # Determine which prompt to use
        first_only_prompt = properties.get("firstOnlyPrompt", "")
        default_prompt = properties.get("defaultPrompt", "")
        main_prompt = properties.get("prompt", "")
        
        # Use first-only prompt on first execution if available
        if execution_count == 0 and first_only_prompt:
            prompt = first_only_prompt
        elif default_prompt:
            prompt = default_prompt
        else:
            prompt = main_prompt
        
        if not prompt:
            return ExecutorResult(
                output=None,
                error="No prompt available for execution",
                metadata={"execution_count": execution_count},
                tokens=TokenUsage(),
                execution_time=time.time() - start_time
            )
        
        # Substitute variables in prompt
        final_prompt = substitute_variables(prompt, inputs)
        
        # Get person details
        service = person_config.get("service", "openai")
        model = person_config.get("modelName") or person_config.get("model")
        api_key_id = person_config.get("apiKeyId")
        system_prompt = person_config.get("systemPrompt", "")
        person_id = person_config.get("id", node_id)
        
        # Check if this is an interactive node
        is_interactive = properties.get("interactive", False)
        
        # Handle context cleaning rule (forgetting) BEFORE making LLM call
        context_cleaning_rule = properties.get("contextCleaningRule", "no_forget")
        
        # Get memory service for forgetting functionality
        from ...utils.dependencies import get_memory_service
        memory_service = get_memory_service()
        
        if memory_service and context_cleaning_rule in ["on_every_turn", "upon_request"]:
            if context_cleaning_rule == "on_every_turn":
                # Forget ALL previous messages (complete forgetting - clears entire conversation)
                memory_service.forget_for_person(person_id)
            elif context_cleaning_rule == "upon_request":
                # Forget only own messages from this specific execution
                if context.execution_id:
                    memory_service.forget_own_messages_for_person(person_id, context.execution_id)
                else:
                    # Fallback to forgetting own messages if no execution_id
                    memory_service.forget_own_messages_for_person(person_id)

        try:
            # Import OutputProcessor here to avoid circular imports
            from ...utils.output_processor import OutputProcessor
            
            # Get conversation history BEFORE making LLM call (after any forgetting)
            conversation_history = memory_service.get_conversation_history(person_id) if memory_service else []
            
            # Build messages array with conversation history + current prompt
            messages = []
            
            # Add conversation history
            if conversation_history:
                messages.extend(conversation_history)
            
            # If we have conversation state inputs, add those messages too
            # This allows debates where different persons can see each other's messages
            for arrow in context.incoming_arrows.get(node_id, []):
                # Check if this arrow carries conversation state
                arrow_data = arrow.get("data", arrow)
                if arrow_data.get("contentType") == "conversation_state":
                    source_id = arrow["source"]
                    if source_id in context.node_outputs:
                        output = context.node_outputs[source_id]
                        if OutputProcessor.is_personjob_output(output):
                            # Get the conversation history from the input
                            input_conversation = OutputProcessor.extract_conversation_history(output)
                            if input_conversation:
                                # Add these messages to our conversation context
                                # They represent the conversation that has happened so far
                                messages.extend(input_conversation)
                            
                            # Also add the latest response as a message
                            latest_text = OutputProcessor.extract_value(output)
                            if latest_text:
                                # Add as user message since it's input to this node
                                messages.append({"role": "user", "content": latest_text})
            
            # Add current prompt as user message
            messages.append({"role": "user", "content": final_prompt})
            
            # Handle interactive mode - wait for user input before proceeding
            if is_interactive and context.interactive_handler:
                logger.info(f"PersonJob {node_id} requesting interactive input")
                
                # Send interactive prompt request
                user_response = await context.interactive_handler(
                    node_id=node_id,
                    prompt=final_prompt,
                    context={
                        "person_id": person_id,
                        "person_name": properties.get("label", person_config.get("name", "Person")),
                        "model": model,
                        "service": service,
                        "execution_count": execution_count
                    }
                )
                
                # If user provided input, add it to the conversation
                if user_response:
                    messages.append({"role": "user", "content": user_response})
                    # Also update the prompt for memory tracking
                    final_prompt = f"{final_prompt}\n\nUser response: {user_response}"
            
            # Make LLM call
            logger.debug(f"PersonJob {node_id} executing: count={execution_count}, max_iterations={max_iterations}, history_messages={len(conversation_history)}, prompt={final_prompt[:50]}...")
            response = await self.llm_service.call_llm(
                service=service,
                api_key_id=api_key_id,
                model=model,
                messages=messages,
                system_prompt=system_prompt
            )
            
            execution_time = time.time() - start_time
            
            # Import OutputProcessor here to avoid circular imports
            from ...utils.output_processor import OutputProcessor
            
            # Add messages to conversation memory if we have an execution_id
            if context.execution_id and memory_service:
                # Add user message (the prompt)
                memory_service.add_message_to_conversation(
                    content=final_prompt,
                    sender_person_id="user",  # System/user prompt
                    execution_id=context.execution_id,
                    participant_person_ids=[person_id],
                    role="user",
                    node_id=node_id,
                    node_label=properties.get("label", "PersonJob")
                )
                
                # Add assistant message (the response)
                # Extract token usage properly
                token_usage = TokenUsage.from_response(response)
                memory_service.add_message_to_conversation(
                    content=response["response"],
                    sender_person_id=person_id,
                    execution_id=context.execution_id,
                    participant_person_ids=[person_id],
                    role="assistant",
                    node_id=node_id,
                    node_label=properties.get("label", "PersonJob"),
                    token_count=token_usage.total,
                    input_tokens=token_usage.input,
                    output_tokens=token_usage.output,
                    cached_tokens=token_usage.cached
                )
            
            # Create structured output with the full conversation that was sent to the LLM
            # This includes both the person's own history and any conversation state from inputs
            # Remove the final user prompt from the messages to get just the conversation history
            full_conversation_history = messages[:-1] if messages else []
            
            # Use TokenUsage for consistency
            token_usage = TokenUsage.from_response(response)
            structured_output = OutputProcessor.create_personjob_output_from_tokens(
                text=response["response"],
                token_usage=token_usage,
                conversation_history=full_conversation_history,
                model=model,
                execution_time=execution_time
            )
            
            result = ExecutorResult(
                output=structured_output,
                metadata={
                    "person_id": person_id,
                    "service": service,
                    "model": model,
                    "prompt_length": len(final_prompt),
                    "system_prompt_length": len(system_prompt),
                    "execution_count": execution_count + 1,
                    "used_first_only": execution_count == 0 and bool(first_only_prompt),
                    "executionTime": execution_time
                },
                tokens=TokenUsage.from_response(response),
                execution_time=execution_time
            )
            
            # Record first-only consumption after successful execution
            if execution_count == 0 and first_only_prompt:
                context.first_only_consumed[node_id] = True
            
            return result
        
        except Exception as e:
            return ExecutorResult(
                output=None,
                error=f"LLM call failed: {str(e)}",
                metadata={
                    "person_id": person_id,
                    "service": service,
                    "model": model,
                    "execution_count": execution_count,
                    "error": str(e)
                },
                tokens=TokenUsage(),
                execution_time=time.time() - start_time
            )


class PersonBatchJobExecutor(BaseExecutor):
    """
    PersonBatchJob executor for handling batch processing of multiple items.
    Similar to PersonJob but designed for processing lists or batches.
    """
    
    def __init__(self, llm_service: LLMService):
        super().__init__()
        self.llm_service = llm_service
    
    async def validate(self, node: Dict[str, Any], context: 'ExecutionContext') -> ValidationResult:
        """Validate PersonBatchJob node configuration"""
        # Use same validation as PersonJob for now
        person_job_executor = PersonJobExecutor(self.llm_service)
        base_validation = await person_job_executor.validate(node, context)
        
        # Add batch-specific validation using centralized validator
        properties = node.get("properties", {})
        batch_error = validate_positive_integer(
            properties,
            "batchSize",
            min_value=1,
            required=False  # Optional field with default value
        )
        
        if batch_error:
            base_validation.errors.append(batch_error)
            base_validation.is_valid = len(base_validation.errors) == 0
        
        return base_validation
    
    async def execute(self, node: Dict[str, Any], context: 'ExecutionContext') -> ExecutorResult:
        """Execute PersonBatchJob node"""
        start_time = time.time()
        
        properties = node.get("properties", {})
        batch_size = properties.get("batchSize", 1)
        
        # Get input data
        inputs = get_input_values(node, context)
        
        # For now, treat batch job similar to regular person job
        # In future, this could handle actual batching logic
        person_job_executor = PersonJobExecutor(self.llm_service)
        result = await person_job_executor.execute(node, context)
        
        # Update metadata to indicate this was a batch job
        if result.metadata:
            result.metadata.update({
                "node_type": "person_batch_job",
                "batch_size": batch_size,
                "is_batch": True
            })
        
        return result