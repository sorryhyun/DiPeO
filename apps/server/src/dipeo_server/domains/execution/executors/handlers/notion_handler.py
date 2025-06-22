from __future__ import annotations

import json
from typing import Any, Callable, Dict, List

from ..schemas.notion import NotionNodeProps
from dipeo_domain import NotionOperation
from ..types import RuntimeExecutionContext
from ..decorators import node
from ..base import BaseNodeHandler, log_action
from ..executor_utils import process_inputs, substitute_variables

@node(
    node_type="notion",
    schema=NotionNodeProps,
    description="Interact with Notion API for page and database operations",
    requires_services=["notion_service"]
)
class NotionHandler(BaseNodeHandler):
    """Notion handler for API operations."""
    
    async def _execute_core(
        self,
        props: NotionNodeProps,
        context: RuntimeExecutionContext,
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> Any:
        """Execute Notion API operation."""
        notion_service = services["notion_service"]
        
        processed_inputs = process_inputs(inputs)
        
        api_key = None
        if props.apiKeyId and hasattr(context, 'api_keys'):
            api_key_info = context.api_keys.get(props.apiKeyId)
            if isinstance(api_key_info, dict):
                api_key = api_key_info.get('key')
            elif isinstance(api_key_info, str):
                api_key = api_key_info
        
        if not api_key:
            raise RuntimeError(f"API key not found: {props.apiKeyId}")
        
        operations: Dict[NotionOperation, Callable[[], Any]] = {
            NotionOperation.read_page: lambda: self._read_page(props, notion_service, api_key, processed_inputs),
            NotionOperation.query_database: lambda: self._query_database(props, notion_service, api_key, processed_inputs),
            NotionOperation.create_page: lambda: self._create_page(props, notion_service, api_key, processed_inputs),
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
        
        result = await handler()
        
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
        
        variables = {}
        for i, value in enumerate(inputs):
            variables[f"input{i}"] = value
            
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
    
    
    async def _query_database(
        self,
        props: NotionNodeProps,
        notion_service: Any,
        api_key: str,
        inputs: List[Any]
    ) -> Dict[str, Any]:
        """Query a Notion database."""
        database_id = self._substitute_variables(props.databaseId or "", inputs)
        
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
    
