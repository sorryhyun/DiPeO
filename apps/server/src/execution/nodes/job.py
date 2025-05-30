"""Job node executor for LLM operations without memory."""

import structlog
from typing import Any, Dict, List, Tuple, Optional

from .base import BaseNodeExecutor
from ..state import ExecutionState
from ...utils.resolve_utils import render_prompt

logger = structlog.get_logger(__name__)


class JobNodeExecutor(BaseNodeExecutor):
    """Executes Job nodes for stateless LLM operations.
    
    Job nodes perform LLM operations without maintaining conversation
    memory, useful for one-off tasks like summarization or translation.
    """
    
    async def execute(
        self, 
        node: dict, 
        vars_map: Dict[str, Any], 
        inputs: List[Any],
        state: ExecutionState,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute a Job node.
        
        Args:
            node: Node configuration with prompt and LLM settings
            vars_map: Variable mappings for prompt rendering
            inputs: Input values from incoming arrows
            state: Current execution state
            **kwargs: Additional arguments (unused)
            
        Returns:
            Tuple of (llm_response, cost_in_usd)
        """
        node_id = self.get_node_id(node)
        data = self.get_node_data(node)
        
        # Check for subtype first
        sub_type = data.get("subType", "code")
        
        # Handle API tool operations separately
        if sub_type == "api_tool":
            result, cost = await self._execute_api_tool(data, inputs)
            return result, cost
        
        # Handle code execution (default behavior)
        if sub_type == "code" or not data.get("prompt"):
            from ...db_blocks import run_db_block
            result = await run_db_block({
                "subType": "code", 
                "sourceDetails": data.get("sourceDetails", "")
            }, inputs)
            return result, 0.0
        
        # Extract job configuration for LLM calls
        prompt_template = data.get("prompt", "")
        service = data.get("service", "openai")
        model = data.get("model")
        temperature = data.get("temperature", 0.7)
        api_key_id = data.get("apiKey")
        
        if not prompt_template:
            logger.warning(
                "empty_job_prompt",
                node_id=node_id
            )
            return None, 0.0
        
        try:
            # Render the prompt with variables
            rendered_prompt = render_prompt(prompt_template, vars_map)
            
            # Add inputs to prompt if available
            if inputs:
                inputs_text = "\n".join(str(inp) for inp in inputs if inp is not None)
                if inputs_text:
                    rendered_prompt = f"{rendered_prompt}\n\nInputs:\n{inputs_text}"
            
            logger.debug(
                "calling_llm_for_job",
                node_id=node_id,
                service=service,
                model=model,
                prompt_length=len(rendered_prompt)
            )
            
            # Call LLM service
            result = await self.llm_service.call_llm(
                messages=[{"role": "user", "content": rendered_prompt}],
                service=service,
                model=model,
                temperature=temperature,
                api_key_id=api_key_id
            )
            
            response = result.get("response")
            cost = result.get("cost", 0.0)
            
            logger.info(
                "job_executed",
                node_id=node_id,
                cost=cost,
                response_length=len(response) if response else 0
            )
            
            return response, cost
            
        except Exception as e:
            logger.error(
                "job_execution_failed",
                node_id=node_id,
                error=str(e),
                exc_info=True
            )
            raise
    
    async def _execute_api_tool(self, data: dict, inputs: list) -> tuple:
        """Execute API tool operations like Notion integration."""
        import json
        
        # Parse the sourceDetails JSON string to get the API configuration
        source_details = data.get("sourceDetails", "{}")
        logger.debug("api_tool_raw_config", source_details=source_details)
        
        try:
            api_config = json.loads(source_details) if isinstance(source_details, str) else source_details
        except json.JSONDecodeError:
            raise ValueError(f"Invalid API configuration JSON: {source_details}")
        
        logger.debug("api_tool_parsed_config", config=api_config)
        api_type = api_config.get("apiType", "")
        logger.debug("api_tool_type", api_type=api_type)
        
        if api_type == "notion":
            return await self._execute_notion_api(api_config, inputs)
        elif api_type == "web_search":
            return await self._execute_web_search_api(api_config, inputs)
        else:
            raise ValueError(f"Unknown API type: '{api_type}'. Available types: 'notion', 'web_search'")
    
    async def _execute_notion_api(self, api_config: dict, inputs: list) -> tuple:
        """Execute Notion API operations."""
        import yaml
        import os
        from ...services.notion_service import NotionService
        
        notion_service = NotionService()
        action = api_config.get("action", "query_database")
        
        # Get API key from the prompts/notion.yaml file
        notion_yaml_path = os.path.join(os.path.dirname(__file__), "../../../../prompts/notion.yaml")
        try:
            with open(notion_yaml_path, "r") as f:
                notion_config = yaml.safe_load(f)
                api_key = notion_config.get("token", "")
        except FileNotFoundError:
            raise ValueError("Notion configuration file not found")
        
        if action == "query_database":
            database_id = api_config.get("databaseId", "")
            filter_obj = api_config.get("filter", None)
            sorts = api_config.get("sorts", None)
            
            if not database_id:
                raise ValueError("Database ID is required for Notion query")
            
            result = await notion_service.query_database(
                api_key=api_key,
                database_id=database_id,
                filter_obj=filter_obj,
                sorts=sorts
            )
            return result, 0.0
        
        # Add other Notion actions as needed...
        else:
            raise ValueError(f"Unknown Notion action: {action}")
    
    async def _execute_web_search_api(self, api_config: dict, inputs: list) -> tuple:
        """Execute web search API operations."""
        from ...services.web_search_service import WebSearchService
        
        search_service = WebSearchService()
        
        # Get search query from config or inputs
        query = api_config.get("query", "")
        if inputs and isinstance(inputs[0], str):
            query = inputs[0]
        
        if not query:
            raise ValueError("Search query is required")
        
        # Get API key
        api_key_id = api_config.get("apiKeyId")
        if api_key_id:
            api_key_data = self.llm_service.api_key_service.get_api_key(api_key_id)
            api_key = api_key_data["key"]
        else:
            raise ValueError("API key is required for web search")
        
        # Perform search
        provider = api_config.get("provider", "serper")
        num_results = api_config.get("numResults", 10)
        
        results = await search_service.search(
            query=query,
            api_key=api_key,
            provider=provider,
            num_results=num_results
        )
        
        # Format results based on configuration
        format_type = api_config.get("outputFormat", "full")
        if format_type == "urls_only":
            formatted_results = [r.get("link") for r in results.get("organic", [])]
        elif format_type == "snippets":
            formatted_results = [{"title": r.get("title"), "snippet": r.get("snippet")}
                               for r in results.get("organic", [])]
        else:
            formatted_results = results
        
        return formatted_results, 0.0