"""
Job node executor for stateless LLM operations.
Handles LLM calls without memory, code execution, and API tool operations.
"""
from typing import Any, Dict, Optional
import json
import logging

from .base_executor import BaseExecutor
from ...constants import NodeType
from ...utils.resolve_utils import render_prompt

logger = logging.getLogger(__name__)


class JobExecutor(BaseExecutor):
    """Executes Job nodes for stateless operations."""
    
    node_type = NodeType.JOB
    
    async def validate_inputs(self, inputs: Dict[str, Any]) -> None:
        """Validate Job node inputs."""
        data = self.node.get('data', {})
        sub_type = data.get('subType', 'code')
        
        if sub_type == 'api_tool':
            # Validate API tool configuration
            source_details = data.get('sourceDetails', '{}')
            try:
                api_config = json.loads(source_details) if isinstance(source_details, str) else source_details
                api_type = api_config.get('apiType')
                if not api_type:
                    raise ValueError("API tool requires 'apiType' specification")
            except json.JSONDecodeError:
                raise ValueError(f"Invalid API configuration JSON: {source_details}")
        elif sub_type == 'llm' or data.get('prompt'):
            # Validate LLM configuration
            if not data.get('prompt'):
                raise ValueError("LLM job requires 'prompt' specification")
            if not data.get('apiKey'):
                raise ValueError("LLM job requires API key selection")
    
    async def execute_node(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the Job node logic."""
        data = self.node.get('data', {})
        sub_type = data.get('subType', 'code')
        
        # Handle different job types
        if sub_type == 'api_tool':
            return await self._execute_api_tool(data, inputs)
        elif sub_type == 'code' or not data.get('prompt'):
            return await self._execute_code(data, inputs)
        else:
            # LLM job
            return await self._execute_llm_job(data, inputs)
    
    async def _execute_code(self, data: dict, inputs: dict) -> dict:
        """Execute code-based job."""
        from ...db_blocks import run_db_block
        
        input_list = self._prepare_inputs(inputs)
        
        result = await run_db_block({
            'subType': 'code',
            'sourceDetails': data.get('sourceDetails', '')
        }, input_list)
        
        return {
            'value': result,
            'cost': 0.0
        }
    
    async def _execute_llm_job(self, data: dict, inputs: dict) -> dict:
        """Execute LLM-based job."""
        prompt_template = data.get('prompt', '')
        service = data.get('service', 'openai')
        model = data.get('model')
        temperature = data.get('temperature', 0.7)
        api_key_id = data.get('apiKey')
        
        # Create vars_map from context outputs
        vars_map = {}
        for node_id, output in self.context.outputs.items():
            vars_map[node_id] = self._resolve_value(f"{{{{{node_id}}}}}")
        
        # Render the prompt
        rendered_prompt = render_prompt(prompt_template, vars_map)
        
        # Add inputs to prompt if available
        input_list = self._prepare_inputs(inputs)
        if input_list:
            inputs_text = "\n".join(str(inp) for inp in input_list if inp is not None)
            if inputs_text:
                rendered_prompt = f"{rendered_prompt}\n\nInputs:\n{inputs_text}"
        
        logger.debug(f"Calling LLM for job {self.node_id}")
        
        # Call LLM service
        result = await self.llm_service.call_llm(
            messages=[{"role": "user", "content": rendered_prompt}],
            service=service,
            model=model,
            temperature=temperature,
            api_key_id=api_key_id
        )
        
        response = result.get('response')
        cost = result.get('cost', 0.0)
        
        return {
            'value': response,
            'cost': cost
        }
    
    async def _execute_api_tool(self, data: dict, inputs: dict) -> dict:
        """Execute API tool operations."""
        source_details = data.get('sourceDetails', '{}')
        api_config = json.loads(source_details) if isinstance(source_details, str) else source_details
        api_type = api_config.get('apiType', '')
        
        input_list = self._prepare_inputs(inputs)
        
        if api_type == 'notion':
            return await self._execute_notion_api(api_config, input_list)
        elif api_type == 'web_search':
            return await self._execute_web_search_api(api_config, input_list)
        else:
            raise ValueError(f"Unknown API type: '{api_type}'")
    
    async def _execute_notion_api(self, api_config: dict, inputs: list) -> dict:
        """Execute Notion API operations."""
        import yaml
        import os
        from ...services.notion_service import NotionService
        
        notion_service = NotionService()
        action = api_config.get('action', 'query_database')
        
        # Get API key from configuration
        notion_yaml_path = os.path.join(os.path.dirname(__file__), '../../../../prompts/notion.yaml')
        try:
            with open(notion_yaml_path, 'r') as f:
                notion_config = yaml.safe_load(f)
                api_key = notion_config.get('token', '')
        except FileNotFoundError:
            raise ValueError("Notion configuration file not found")
        
        if action == 'query_database':
            database_id = api_config.get('databaseId', '')
            filter_obj = api_config.get('filter', None)
            sorts = api_config.get('sorts', None)
            
            if not database_id:
                raise ValueError("Database ID is required for Notion query")
            
            result = await notion_service.query_database(
                api_key=api_key,
                database_id=database_id,
                filter_obj=filter_obj,
                sorts=sorts
            )
            return {'value': result, 'cost': 0.0}
        else:
            raise ValueError(f"Unknown Notion action: {action}")
    
    async def _execute_web_search_api(self, api_config: dict, inputs: list) -> dict:
        """Execute web search API operations."""
        from ...services.web_search_service import WebSearchService
        
        search_service = WebSearchService()
        
        # Get search query
        query = api_config.get('query', '')
        if inputs and isinstance(inputs[0], str):
            query = inputs[0]
        
        if not query:
            raise ValueError("Search query is required")
        
        # Get API key
        api_key_id = api_config.get('apiKeyId')
        if api_key_id:
            api_key_data = self.llm_service.api_key_service.get_api_key(api_key_id)
            api_key = api_key_data['key']
        else:
            raise ValueError("API key is required for web search")
        
        # Perform search
        provider = api_config.get('provider', 'serper')
        num_results = api_config.get('numResults', 10)
        
        results = await search_service.search(
            query=query,
            api_key=api_key,
            provider=provider,
            num_results=num_results
        )
        
        # Format results
        format_type = api_config.get('outputFormat', 'full')
        if format_type == 'urls_only':
            formatted_results = [r.get('link') for r in results.get('organic', [])]
        elif format_type == 'snippets':
            formatted_results = [{'title': r.get('title'), 'snippet': r.get('snippet')}
                               for r in results.get('organic', [])]
        else:
            formatted_results = results
        
        return {'value': formatted_results, 'cost': 0.0}