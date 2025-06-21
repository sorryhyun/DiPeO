"""
Simple node definitions that combine schema and handler.
These are nodes with minimal logic that don't require separate files.
"""

from typing import Dict, Any, Optional, Union
from pydantic import Field, field_validator
import json
import asyncio
import logging

from .schemas.base import BaseNodeProps
from dipeo_domain import ExecutionContext, NodeOutput
from .executor_utils import substitute_variables
from .decorators import node

logger = logging.getLogger(__name__)


# Start Node
class StartNodeProps(BaseNodeProps):
    """Properties for Start node type."""
    
    data: Optional[Union[str, Dict[str, Any], list]] = Field(
        None, 
        description="Initial data to provide to the workflow"
    )
    
    @field_validator('data', mode='before')
    def parse_data(cls, v):
        """Parse data if it's a JSON string."""
        if isinstance(v, str):
            try:
                # Try to parse as JSON
                return json.loads(v)
            except json.JSONDecodeError:
                # Keep as string if not valid JSON
                return v
        return v
    
    def get_output(self) -> Any:
        """Get the output data for this start node."""
        return self.data if self.data is not None else {}


@node(
    node_type="start",
    schema=StartNodeProps,
    description="Provides initial data to the workflow"
)
async def start_handler(
    props: StartNodeProps,
    context: ExecutionContext,
    inputs: Dict[str, Any]
) -> NodeOutput:
    """
    Handle Start node execution.
    
    Start nodes provide initial data to the workflow.
    They don't process inputs from other nodes.
    """
    logger.debug(f"Executing start node with data: {props.data}")
    
    # Start nodes simply output their configured data
    output = props.get_output()
    
    logger.info(f"Start node output: {output}")
    
    return NodeOutput(
        value=output,
        metadata={"node_type": "start"}
    )


# UserResponse Node
class UserResponseNodeProps(BaseNodeProps):
    """Properties for UserResponse node"""
    prompt: str = Field(..., description="Prompt to display to the user")
    timeout: Optional[float] = Field(
        10,
        ge=1,
        le=60,
        description="Timeout in seconds for user response"
    )


@node(
    node_type="user_response",
    schema=UserResponseNodeProps,
    description="Prompts user for interactive input"
)
async def user_response_handler(
    props: UserResponseNodeProps,
    context: ExecutionContext,
    inputs: Dict[str, Any]
) -> NodeOutput:
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
                return NodeOutput(
                    value={
                        "response": response,
                        "timeout": False,
                        "prompt": processed_prompt
                    },
                    metadata={
                        "timeout_seconds": props.timeout,
                        "user_responded": True,
                        "node_type": "user_response"
                    }
                )
                
            except asyncio.TimeoutError:
                # Handle timeout
                logger.info(f"User response timeout for node {node_id} after {props.timeout} seconds")
                
                return NodeOutput(
                    value={
                        "response": None,
                        "timeout": True,
                        "prompt": processed_prompt
                    },
                    metadata={
                        "timeout_seconds": props.timeout,
                        "user_responded": False,
                        "node_type": "user_response"
                    }
                )
        else:
            # No interactive handler available - return timeout
            logger.warning(f"No interactive handler available for user response in node {node_id}")
            return NodeOutput(
                value={
                    "response": None,
                    "timeout": True,
                    "prompt": processed_prompt,
                    "error": "No interactive handler available"
                },
                metadata={
                    "timeout_seconds": props.timeout,
                    "user_responded": False,
                    "node_type": "user_response"
                }
            )
            
    except Exception as e:
        logger.error(f"Error in user_response node {node_id}: {str(e)}")
        return NodeOutput(
            value={
                "response": None,
                "timeout": False,
                "prompt": processed_prompt,
                "error": str(e)
            },
            metadata={
                "timeout_seconds": props.timeout,
                "user_responded": False,
                "node_type": "user_response"
            }
        )


# Node definitions are now registered via decorators