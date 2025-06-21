"""Refactored Notion handler using BaseNodeHandler."""

from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from ..schemas.notion import NotionNodeProps, NotionOperation
from ..types import RuntimeExecutionContext
from ..decorators import node
from ..utils import BaseNodeHandler, process_inputs, get_api_key, log_action, substitute_variables


@node(
    node_type="notion",
    schema=NotionNodeProps,
    description="Interact with Notion API for page and database operations",
    requires_services=["notion_service"]
)
class NotionHandler(BaseNodeHandler):
    """Notion handler for API operations.
    
    This refactored version eliminates ~50 lines of boilerplate by:
    - Inheriting error handling, timing, and service validation
    - Simplified operation dispatch
    - Automatic metadata building
    """
    
    async def _execute_core(
        self,
        props: NotionNodeProps,
        context: RuntimeExecutionContext,
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> Any:
        """Execute Notion API operation."""
        notion_service = services["notion_service"]
        
        # Process inputs to extract values
        processed_inputs = process_inputs(inputs)
        
        # Get API key
        api_key = get_api_key(props.apiKeyId, context)
        if not api_key:
            raise RuntimeError(f"API key not found: {props.apiKeyId}")
        
        # Define operation handlers
        operations: Dict[NotionOperation, Callable[[], Any]] = {
            NotionOperation.READ_PAGE: lambda: self._read_page(props, notion_service, api_key, processed_inputs),
            NotionOperation.LIST_BLOCKS: lambda: self._list_blocks(props, notion_service, api_key, processed_inputs),
            NotionOperation.APPEND_BLOCKS: lambda: self._append_blocks(props, notion_service, api_key, processed_inputs),
            NotionOperation.UPDATE_BLOCK: lambda: self._update_block(props, notion_service, api_key, processed_inputs),
            NotionOperation.QUERY_DATABASE: lambda: self._query_database(props, notion_service, api_key, processed_inputs),
            NotionOperation.CREATE_PAGE: lambda: self._create_page(props, notion_service, api_key, processed_inputs),
            NotionOperation.EXTRACT_TEXT: lambda: self._extract_text(props, notion_service, processed_inputs),
        }
        
        handler = operations.get(props.operation)
        if not handler:
            raise ValueError(f"Unsupported Notion operation: {props.operation}")
        
        log_action(
            self.logger,
            context.current_node_id,
            "Executing Notion operation",
            operation=props.operation.value
        )
        
        # Execute the operation
        result = await handler()
        
        # Store operation type for metadata
        self._operation = props.operation
        
        return result
    
    def _build_metadata(
        self,
        start_time: float,
        props: NotionNodeProps,
        context: RuntimeExecutionContext,
        result: Any
    ) -> Dict[str, Any]:
        """Build Notion-specific metadata."""
        metadata = super()._build_metadata(start_time, props, context, result)
        
        if hasattr(self, '_operation'):
            metadata["operation"] = self._operation.value
            delattr(self, '_operation')
        
        return metadata
    
    def _substitute_variables(self, text: str, inputs: List[Any]) -> str:
        """Helper to substitute variables in text using input values."""
        if not text:
            return text
        
        # Create mapping from inputs
        variables = {}
        for i, value in enumerate(inputs):
            variables[f"input{i}"] = value
            
            # Also support named variables if the input is a dict
            if isinstance(value, dict):
                variables.update(value)
        
        return substitute_variables(text, variables)
    
    async def _read_page(
        self,
        props: NotionNodeProps,
        notion_service: Any,
        api_key: str,
        inputs: List[Any]
    ) -> Dict[str, Any]:
        """Read a Notion page."""
        page_id = self._substitute_variables(props.pageId or "", inputs)
        
        result = await notion_service.retrieve_page(page_id, api_key)
        self.logger.debug(f"Retrieved page: {page_id}")
        return result
    
    async def _list_blocks(
        self,
        props: NotionNodeProps,
        notion_service: Any,
        api_key: str,
        inputs: List[Any]
    ) -> Dict[str, Any]:
        """List blocks in a Notion page."""
        page_id = self._substitute_variables(props.pageId or "", inputs)
        
        blocks = await notion_service.list_blocks(page_id, api_key)
        self.logger.debug(f"Listed {len(blocks)} blocks from page: {page_id}")
        return {"blocks": blocks, "count": len(blocks)}
    
    async def _append_blocks(
        self,
        props: NotionNodeProps,
        notion_service: Any,
        api_key: str,
        inputs: List[Any]
    ) -> Dict[str, Any]:
        """Append blocks to a Notion page."""
        page_id = self._substitute_variables(props.pageId or "", inputs)
        blocks_str = self._substitute_variables(props.blocks or "[]", inputs)
        
        blocks = json.loads(blocks_str)
        result = await notion_service.append_blocks(page_id, blocks, api_key)
        self.logger.debug(f"Appended {len(blocks)} blocks to page: {page_id}")
        return result
    
    async def _update_block(
        self,
        props: NotionNodeProps,
        notion_service: Any,
        api_key: str,
        inputs: List[Any]
    ) -> Dict[str, Any]:
        """Update a Notion block."""
        block_id = self._substitute_variables(props.blockId or "", inputs)
        block_data_str = self._substitute_variables(props.blockData or "{}", inputs)
        
        block_data = json.loads(block_data_str)
        result = await notion_service.update_block(block_id, block_data, api_key)
        self.logger.debug(f"Updated block: {block_id}")
        return result
    
    async def _query_database(
        self,
        props: NotionNodeProps,
        notion_service: Any,
        api_key: str,
        inputs: List[Any]
    ) -> Dict[str, Any]:
        """Query a Notion database."""
        database_id = self._substitute_variables(props.databaseId or "", inputs)
        
        # Parse filter and sorts if provided
        filter_obj = None
        if props.filter:
            filter_str = self._substitute_variables(props.filter, inputs)
            filter_obj = json.loads(filter_str)
        
        sorts_obj = None
        if props.sorts:
            sorts_str = self._substitute_variables(props.sorts, inputs)
            sorts_obj = json.loads(sorts_str)
        
        results = await notion_service.query_database(
            database_id, filter_obj, sorts_obj, api_key
        )
        self.logger.debug(f"Queried database {database_id}, found {len(results)} results")
        return {"results": results, "count": len(results)}
    
    async def _create_page(
        self,
        props: NotionNodeProps,
        notion_service: Any,
        api_key: str,
        inputs: List[Any]
    ) -> Dict[str, Any]:
        """Create a new Notion page."""
        parent_str = self._substitute_variables(props.parentConfig or "{}", inputs)
        properties_str = self._substitute_variables(props.pageProperties or "{}", inputs)
        
        parent = json.loads(parent_str)
        page_properties = json.loads(properties_str)
        
        children = None
        if props.children:
            children_str = self._substitute_variables(props.children, inputs)
            children = json.loads(children_str)
        
        result = await notion_service.create_page(
            parent, page_properties, children, api_key
        )
        self.logger.debug("Created new Notion page")
        return result
    
    async def _extract_text(
        self,
        props: NotionNodeProps,
        notion_service: Any,
        inputs: List[Any]
    ) -> Dict[str, Any]:
        """Extract text from Notion blocks in input."""
        # Look for blocks in the inputs
        blocks = None
        
        for input_data in inputs:
            if isinstance(input_data, dict) and "blocks" in input_data:
                blocks = input_data["blocks"]
                break
        
        if blocks:
            text = notion_service.extract_text_from_blocks(blocks)
            self.logger.debug(f"Extracted text from {len(blocks)} blocks")
            return {"text": text, "block_count": len(blocks)}
        else:
            self.logger.warning("No blocks found in input for text extraction")
            return {"text": "", "block_count": 0, "error": "No blocks found in input"}