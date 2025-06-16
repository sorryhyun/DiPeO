"""
Notion node handler - handles Notion API operations
"""

import json
import logging
from typing import Dict, Any, List, Optional
from ..schemas.notion import NotionNodeProps, NotionOperation
from ..types import ExecutionContext

logger = logging.getLogger(__name__)


async def notion_handler(
    props: NotionNodeProps,
    context: ExecutionContext,
    inputs: Dict[str, Any]
) -> Any:
    """Handle Notion node execution for various API operations"""
    
    operation = props.operation
    api_key_id = props.apiKeyId
    
    logger.info(f"Executing Notion operation: {operation}")
    
    # Check if Notion service is available
    if not hasattr(context, 'notion_service'):
        raise RuntimeError("Notion service not available in context")
    
    # Get API key from context
    api_key = _get_api_key(api_key_id, context)
    if not api_key:
        raise RuntimeError(f"API key '{api_key_id}' not found or invalid")
    
    try:
        # Process inputs for variable substitution
        processed_inputs = _process_inputs(inputs)
        
        # Execute operation based on type
        if operation == NotionOperation.READ_PAGE:
            result = await _read_page(props, context, api_key, processed_inputs)
        
        elif operation == NotionOperation.LIST_BLOCKS:
            result = await _list_blocks(props, context, api_key, processed_inputs)
        
        elif operation == NotionOperation.APPEND_BLOCKS:
            result = await _append_blocks(props, context, api_key, processed_inputs)
        
        elif operation == NotionOperation.UPDATE_BLOCK:
            result = await _update_block(props, context, api_key, processed_inputs)
        
        elif operation == NotionOperation.QUERY_DATABASE:
            result = await _query_database(props, context, api_key, processed_inputs)
        
        elif operation == NotionOperation.CREATE_PAGE:
            result = await _create_page(props, context, api_key, processed_inputs)
        
        elif operation == NotionOperation.EXTRACT_TEXT:
            result = await _extract_text(props, context, processed_inputs)
        
        else:
            raise ValueError(f"Unknown operation: {operation}")
        
        logger.info(f"Notion operation completed successfully")
        return result
        
    except Exception as e:
        error_msg = f"Notion operation failed: {str(e)}"
        logger.error(error_msg, exc_info=True)
        raise RuntimeError(error_msg)


def _get_api_key(api_key_id: str, context: ExecutionContext) -> Optional[str]:
    """Get API key from context"""
    if not hasattr(context, 'api_keys'):
        return None
    
    api_key_info = context.api_keys.get(api_key_id)
    if isinstance(api_key_info, dict):
        return api_key_info.get('key')
    return api_key_info if isinstance(api_key_info, str) else None


def _process_inputs(inputs: Dict[str, Any]) -> List[Any]:
    """Process inputs to extract values and handle special output types"""
    if not inputs:
        return []
    
    processed = []
    for value in inputs.values():
        # Handle PersonJob outputs
        if isinstance(value, dict) and "output" in value and "conversation_history" in value:
            processed.append(value.get("output"))
        else:
            processed.append(value)
    
    return processed


def _substitute_variables(text: str, inputs: List[Any]) -> str:
    """Substitute variables in text with input values"""
    from ..executor_utils import substitute_variables
    
    if not text:
        return text
    
    # Create a mapping of variables to values for the shared function
    variables = {}
    for i, value in enumerate(inputs):
        variables[f"input{i}"] = value
        
        # Also support named variables if the input is a dict
        if isinstance(value, dict):
            variables.update(value)
    
    return substitute_variables(text, variables)


async def _read_page(
    props: NotionNodeProps, 
    context: ExecutionContext, 
    api_key: str,
    inputs: List[Any]
) -> Dict[str, Any]:
    """Read a Notion page"""
    page_id = _substitute_variables(props.pageId or "", inputs)
    
    result = await context.notion_service.retrieve_page(page_id, api_key)
    logger.debug(f"Retrieved page: {page_id}")
    return result


async def _list_blocks(
    props: NotionNodeProps,
    context: ExecutionContext,
    api_key: str,
    inputs: List[Any]
) -> Dict[str, Any]:
    """List blocks in a Notion page"""
    page_id = _substitute_variables(props.pageId or "", inputs)
    
    blocks = await context.notion_service.list_blocks(page_id, api_key)
    logger.debug(f"Listed {len(blocks)} blocks from page: {page_id}")
    return {"blocks": blocks, "count": len(blocks)}


async def _append_blocks(
    props: NotionNodeProps,
    context: ExecutionContext,
    api_key: str,
    inputs: List[Any]
) -> Dict[str, Any]:
    """Append blocks to a Notion page"""
    page_id = _substitute_variables(props.pageId or "", inputs)
    blocks_str = _substitute_variables(props.blocks or "[]", inputs)
    
    blocks = json.loads(blocks_str)
    result = await context.notion_service.append_blocks(page_id, blocks, api_key)
    logger.debug(f"Appended {len(blocks)} blocks to page: {page_id}")
    return result


async def _update_block(
    props: NotionNodeProps,
    context: ExecutionContext,
    api_key: str,
    inputs: List[Any]
) -> Dict[str, Any]:
    """Update a Notion block"""
    block_id = _substitute_variables(props.blockId or "", inputs)
    block_data_str = _substitute_variables(props.blockData or "{}", inputs)
    
    block_data = json.loads(block_data_str)
    result = await context.notion_service.update_block(block_id, block_data, api_key)
    logger.debug(f"Updated block: {block_id}")
    return result


async def _query_database(
    props: NotionNodeProps,
    context: ExecutionContext,
    api_key: str,
    inputs: List[Any]
) -> Dict[str, Any]:
    """Query a Notion database"""
    database_id = _substitute_variables(props.databaseId or "", inputs)
    
    # Parse filter and sorts if provided
    filter_obj = None
    if props.filter:
        filter_str = _substitute_variables(props.filter, inputs)
        filter_obj = json.loads(filter_str)
    
    sorts_obj = None
    if props.sorts:
        sorts_str = _substitute_variables(props.sorts, inputs)
        sorts_obj = json.loads(sorts_str)
    
    results = await context.notion_service.query_database(
        database_id, filter_obj, sorts_obj, api_key
    )
    logger.debug(f"Queried database {database_id}, found {len(results)} results")
    return {"results": results, "count": len(results)}


async def _create_page(
    props: NotionNodeProps,
    context: ExecutionContext,
    api_key: str,
    inputs: List[Any]
) -> Dict[str, Any]:
    """Create a new Notion page"""
    parent_str = _substitute_variables(props.parentConfig or "{}", inputs)
    properties_str = _substitute_variables(props.pageProperties or "{}", inputs)
    
    parent = json.loads(parent_str)
    page_properties = json.loads(properties_str)
    
    children = None
    if props.children:
        children_str = _substitute_variables(props.children, inputs)
        children = json.loads(children_str)
    
    result = await context.notion_service.create_page(
        parent, page_properties, children, api_key
    )
    logger.debug("Created new Notion page")
    return result


async def _extract_text(
    props: NotionNodeProps,
    context: ExecutionContext,
    inputs: List[Any]
) -> Dict[str, Any]:
    """Extract text from Notion blocks in input"""
    # Look for blocks in the inputs
    blocks = None
    
    for input_data in inputs:
        if isinstance(input_data, dict) and "blocks" in input_data:
            blocks = input_data["blocks"]
            break
    
    if blocks:
        text = context.notion_service.extract_text_from_blocks(blocks)
        logger.debug(f"Extracted text from {len(blocks)} blocks")
        return {"text": text, "block_count": len(blocks)}
    else:
        logger.warning("No blocks found in input for text extraction")
        return {"text": "", "block_count": 0, "error": "No blocks found in input"}