"""
PersonJob node executor - handles LLM API calls with person configuration
"""

from typing import Dict, Any
import time
import logging

from .base_executor import BaseExecutor, ValidationResult, ExecutorResult
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
        
        if not person_config and not person_id:
            errors.append("Either person configuration or personId is required")
        elif person_config:
            # Check required person fields
            service = person_config.get("service", "openai")
            model = person_config.get("modelName") or person_config.get("model")
            api_key_id = person_config.get("apiKeyId")
            
            if not api_key_id:
                errors.append("API key ID is required in person configuration")
            
            if not model:
                errors.append("Model name is required in person configuration")
            
            if service not in ["openai", "claude", "gemini", "grok"]:
                warnings.append(f"Unsupported service: {service}")
        
        # Validate prompt
        prompt = properties.get("prompt", "")
        default_prompt = properties.get("defaultPrompt", "")
        
        if not prompt and not default_prompt:
            errors.append("Either prompt or defaultPrompt is required")
        
        # Check max iterations
        max_iterations = properties.get("iterationCount")
        if max_iterations is not None:
            if not isinstance(max_iterations, int) or max_iterations < 1:
                errors.append("iterationCount must be a positive integer")
        
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
        inputs = self.get_input_values(node, context)
        
        # Check iteration count and handle first-only logic
        execution_count = context.node_execution_counts.get(node_id, 0)
        max_iterations = properties.get("iterationCount")
        
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
                cost=0.0,
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
                cost=0.0,
                execution_time=time.time() - start_time
            )
        
        # Substitute variables in prompt
        final_prompt = self.substitute_variables(prompt, inputs)
        
        # Get person details
        service = person_config.get("service", "openai")
        model = person_config.get("modelName") or person_config.get("model")
        api_key_id = person_config.get("apiKeyId")
        system_prompt = person_config.get("systemPrompt", "")
        person_id = person_config.get("id", node_id)
        
        try:
            # Make LLM call
            logger.debug(f"PersonJob {node_id} executing: count={execution_count}, max_iterations={max_iterations}, prompt={final_prompt[:50]}...")
            response = await self.llm_service.call_llm(
                service=service,
                api_key_id=api_key_id,
                model=model,
                messages=final_prompt,
                system_prompt=system_prompt
            )
            
            execution_time = time.time() - start_time
            
            return ExecutorResult(
                output=response["response"],
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
                cost=response.get("cost", 0.0),
                tokens_used=response.get("tokens_used"),
                execution_time=execution_time
            )
        
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
                cost=0.0,
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
        
        # Add batch-specific validation
        properties = node.get("properties", {})
        batch_size = properties.get("batchSize", 1)
        
        if not isinstance(batch_size, int) or batch_size < 1:
            base_validation.errors.append("batchSize must be a positive integer")
            base_validation.is_valid = False
        
        return base_validation
    
    async def execute(self, node: Dict[str, Any], context: 'ExecutionContext') -> ExecutorResult:
        """Execute PersonBatchJob node"""
        start_time = time.time()
        
        properties = node.get("properties", {})
        batch_size = properties.get("batchSize", 1)
        
        # Get input data
        inputs = self.get_input_values(node, context)
        
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