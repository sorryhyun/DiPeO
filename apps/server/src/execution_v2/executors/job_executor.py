"""Job node executor for stateless operations."""

from typing import Any, Dict, Tuple, Optional
import json
import logging

from .base_executor import BaseExecutor
from ..core.execution_context import ExecutionContext
from ..core.skip_manager import SkipManager
from ...utils.resolve_utils import render_prompt

logger = logging.getLogger(__name__)


class JobExecutor(BaseExecutor):
    """Executor for Job nodes - handles stateless operations."""
    
    def __init__(self, context: ExecutionContext, llm_service=None, memory_service=None):
        """Initialize the job executor."""
        super().__init__(context, llm_service, memory_service)

    async def validate_inputs(
        self,
        node: Dict[str, Any],
        context: ExecutionContext
    ) -> Optional[str]:
        """Validate Job node inputs.
        
        Args:
            node: The node configuration
            context: The execution context
            
        Returns:
            Error message if validation fails, None if valid
        """
        data = node.get('data', {})
        sub_type = data.get('subType', 'code')
        
        if sub_type == 'api_tool':
            # Validate API tool configuration
            source_details = data.get('sourceDetails', '{}')
            try:
                api_config = json.loads(source_details) if isinstance(source_details, str) else source_details
                api_type = api_config.get('apiType')
                if not api_type:
                    return "API tool requires 'apiType' specification"
            except json.JSONDecodeError:
                return f"Invalid API configuration JSON: {source_details}"
        elif sub_type == 'llm' or data.get('prompt'):
            # Validate LLM configuration
            if not data.get('prompt'):
                return "LLM job requires 'prompt' specification"
            if not data.get('apiKey'):
                return "LLM job requires API key selection"
        
        return None

    async def execute(
        self,
        node: Dict[str, Any],
        context: ExecutionContext,
        skip_manager: SkipManager,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute a Job node.
        
        Args:
            node: The node configuration
            context: The execution context
            skip_manager: The skip manager (not used here)
            **kwargs: Additional arguments
            
        Returns:
            Tuple of (result, cost)
        """
        data = node.get('data', {})
        sub_type = data.get('subType', 'code')
        
        # Prepare inputs
        inputs = self._prepare_inputs(node, context)
        
        # Handle different job types
        if sub_type == 'api_tool':
            result, cost = await self._execute_api_tool(data, inputs, context)
        elif sub_type == 'code' or not data.get('prompt'):
            result, cost = await self._execute_code(data, inputs, context)
        else:
            # LLM job
            result, cost = await self._execute_llm_job(data, inputs, context)
        
        return result, cost

    async def _execute_code(self, data: dict, inputs: dict, context: ExecutionContext) -> Tuple[Any, float]:
        """Execute code-based job."""
        from ...db_blocks import run_db_block
        
        # Convert inputs dict to list format
        input_list = []
        for key, value in inputs.items():
            if value is not None:
                input_list.append(value)
        
        result = await run_db_block({
            'subType': 'code',
            'sourceDetails': data.get('sourceDetails', '')
        }, input_list)
        
        return result, 0.0

    async def _execute_llm_job(self, data: dict, inputs: dict, context: ExecutionContext) -> Tuple[Any, float]:
        """Execute LLM-based job."""
        prompt_template = data.get('prompt', '')
        service = data.get('service', 'openai')
        model = data.get('model')
        temperature = data.get('temperature', 0.7)
        api_key_id = data.get('apiKey')
        
        # Create vars_map from context outputs
        vars_map = {}
        for node_id, output in context.node_outputs.items():
            vars_map[node_id] = output
        
        # Render the prompt
        rendered_prompt = render_prompt(prompt_template, vars_map)
        
        # Add inputs to prompt if available
        input_list = []
        for key, value in inputs.items():
            if value is not None:
                input_list.append(value)
        
        if input_list:
            inputs_text = "\n".join(str(inp) for inp in input_list if inp is not None)
            if inputs_text:
                rendered_prompt = f"{rendered_prompt}\n\nInputs:\n{inputs_text}"
        
        logger.debug(f"Calling LLM for job node")
        
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
        
        return response, cost

    async def _execute_api_tool(self, data: dict, inputs: dict, context: ExecutionContext) -> Tuple[Any, float]:
        """Execute API tool operations."""
        source_details = data.get('sourceDetails', '{}')
        api_config = json.loads(source_details) if isinstance(source_details, str) else source_details
        api_type = api_config.get('apiType', '')
        
        # Convert inputs dict to list format
        input_list = []
        for key, value in inputs.items():
            if value is not None:
                input_list.append(value)
        
        if api_type == 'notion':
            result = await self._execute_notion_api(api_config, input_list)
        elif api_type == 'web_search':
            result = await self._execute_web_search_api(api_config, input_list)
        else:
            raise ValueError(f"Unknown API type: '{api_type}'")
        
        # Extract result and cost from the old format
        if isinstance(result, dict) and 'value' in result:
            return result['value'], result.get('cost', 0.0)
        else:
            return result, 0.0

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