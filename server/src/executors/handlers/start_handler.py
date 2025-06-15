"""Handler for Start node type."""

from typing import Dict, Any
import logging

from ..schemas.start import StartNodeProps
from ..types import ExecutionContext

logger = logging.getLogger(__name__)


async def start_handler(
    props: StartNodeProps,
    context: ExecutionContext,
    inputs: Dict[str, Any]
) -> Any:
    """
    Handle Start node execution.
    
    Start nodes provide initial data to the workflow.
    They don't process inputs from other nodes.
    """
    logger.debug(f"Executing start node with data: {props.data}")
    
    # Start nodes simply output their configured data
    output = props.get_output()
    
    logger.info(f"Start node output: {output}")
    
    return output