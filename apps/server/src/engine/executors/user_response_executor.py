from typing import Dict, Any, TYPE_CHECKING
import asyncio
from .base_executor import BaseExecutor, ExecutorResult
from .validator import (
    ValidationResult,
    validate_required_fields,
    validate_numeric_range
)
from .utils import get_input_values, substitute_variables
import logging

if TYPE_CHECKING:
    from ..engine import ExecutionContext

logger = logging.getLogger(__name__)


class UserResponseExecutor(BaseExecutor):
    """
    Executor for user_response nodes that wait for user input.
    Shows a prompt to the user and waits for their response with a timeout.
    """
    
    async def validate(self, node: Dict[str, Any], context: 'ExecutionContext') -> ValidationResult:
        """Validate user_response node configuration"""
        errors = []
        warnings = []
        
        # Validate required fields
        props = node.get("properties", {})
        required_fields = ["prompt"]
        field_errors = validate_required_fields(props, required_fields)
        errors.extend(field_errors)
        
        # Validate timeout using centralized function
        timeout_error = validate_numeric_range(
            props,
            "timeout",
            min_value=1,
            max_value=60,
            required=False,
            allow_int=True,
            allow_float=True
        )
        if timeout_error:
            errors.append(timeout_error)
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def execute(self, node: Dict[str, Any], context: 'ExecutionContext') -> ExecutorResult:
        """Execute user_response node - wait for user input"""
        node_id = node.get("id", "unknown")
        props = node.get("properties", {})
        
        # Get prompt and timeout
        prompt = props.get("prompt", "Please provide input:")
        timeout = props.get("timeout", 10)  # Default 10 seconds
        
        # Get input values from incoming connections
        input_values = get_input_values(node, context)
        
        # Substitute variables in prompt
        processed_prompt = substitute_variables(prompt, input_values)
        
        try:
            # Check if we have an interactive handler
            if context.interactive_handler:
                # Use the interactive handler to send prompt and wait for response
                try:
                    # The interactive handler expects node_id, prompt, and context
                    response = await asyncio.wait_for(
                        context.interactive_handler(
                            node_id, 
                            processed_prompt, 
                            {
                                "timeout": timeout,
                                "nodeType": "user_response"
                            }
                        ),
                        timeout=timeout
                    )
                    
                    # User provided response
                    return ExecutorResult(
                        output={
                            "response": response,
                            "timeout": False,
                            "prompt": processed_prompt
                        },
                        metadata={
                            "timeout_seconds": timeout,
                            "user_responded": True
                        }
                    )
                    
                except asyncio.TimeoutError:
                    # Handle timeout
                    logger.info(f"User response timeout for node {node_id} after {timeout} seconds")
                    
                    return ExecutorResult(
                        output={
                            "response": None,
                            "timeout": True,
                            "prompt": processed_prompt
                        },
                        metadata={
                            "timeout_seconds": timeout,
                            "user_responded": False
                        }
                    )
            else:
                # No interactive handler available - return timeout
                logger.warning(f"No interactive handler available for user response in node {node_id}")
                return ExecutorResult(
                    output={
                        "response": None,
                        "timeout": True,
                        "prompt": processed_prompt,
                        "error": "No interactive handler available"
                    },
                    metadata={
                        "timeout_seconds": timeout,
                        "user_responded": False
                    }
                )
                
        except Exception as e:
            logger.error(f"Error in user_response node {node_id}: {str(e)}")
            return ExecutorResult(
                output={
                    "response": None,
                    "timeout": False,
                    "prompt": processed_prompt,
                    "error": str(e)
                },
                error=str(e),
                metadata={
                    "timeout_seconds": timeout,
                    "user_responded": False
                }
            )