"""
Handler for UserResponse nodes - interactive user input
"""

from typing import Dict, Any
import asyncio
import logging

from ..schemas.user_response import UserResponseNodeProps
from ..types import ExecutionContext
from ..executor_utils import substitute_variables

logger = logging.getLogger(__name__)


async def user_response_handler(
    props: UserResponseNodeProps,
    context: ExecutionContext,
    inputs: Dict[str, Any]
) -> Any:
    """Handle UserResponse node execution"""
    
    node_id = context.current_node_id
    
    # Substitute variables in prompt
    processed_prompt = substitute_variables(props.prompt, inputs)
    
    try:
        # Check if we have an interactive handler
        interactive_handler = getattr(context, 'interactive_handler', None)
        
        if interactive_handler:
            # Use the interactive handler to send prompt and wait for response
            try:
                # The interactive handler expects node_id, prompt, and context
                response = await asyncio.wait_for(
                    interactive_handler(
                        node_id, 
                        processed_prompt, 
                        {
                            "timeout": props.timeout,
                            "nodeType": "user_response"
                        }
                    ),
                    timeout=props.timeout
                )
                
                # User provided response
                return {
                    "response": response,
                    "timeout": False,
                    "prompt": processed_prompt,
                    "metadata": {
                        "timeout_seconds": props.timeout,
                        "user_responded": True
                    }
                }
                
            except asyncio.TimeoutError:
                # Handle timeout
                logger.info(f"User response timeout for node {node_id} after {props.timeout} seconds")
                
                return {
                    "response": None,
                    "timeout": True,
                    "prompt": processed_prompt,
                    "metadata": {
                        "timeout_seconds": props.timeout,
                        "user_responded": False
                    }
                }
        else:
            # No interactive handler available - return timeout
            logger.warning(f"No interactive handler available for user response in node {node_id}")
            return {
                "response": None,
                "timeout": True,
                "prompt": processed_prompt,
                "error": "No interactive handler available",
                "metadata": {
                    "timeout_seconds": props.timeout,
                    "user_responded": False
                }
            }
            
    except Exception as e:
        logger.error(f"Error in user_response node {node_id}: {str(e)}")
        return {
            "response": None,
            "timeout": False,
            "prompt": processed_prompt,
            "error": str(e),
            "metadata": {
                "timeout_seconds": props.timeout,
                "user_responded": False
            }
        }