import httpx
from typing import Dict, Any, List, Optional
from ..exceptions import DiagramExecutionError
from ..utils.base_service import BaseService


class WebSearchService(BaseService):
    """Service for web search integration."""

    def __init__(self):
        super().__init__()
        # You can use various search APIs: Google Custom Search, Bing, Serper, etc.
        self.search_providers = {
            'serper': 'https://google.serper.dev/search',
            'bing': 'https://api.bing.microsoft.com/v7.0/search',
            'google': 'https://www.googleapis.com/customsearch/v1'
        }

    async def search(
            self,
            query: str,
            api_key: str,
            provider: str = 'serper',
            num_results: int = 10,
            **kwargs
    ) -> Dict[str, Any]:
        """Perform web search."""
        if provider == 'serper':
            return await self._search_serper(query, api_key, num_results, **kwargs)
        elif provider == 'bing':
            return await self._search_bing(query, api_key, num_results, **kwargs)
        else:
            raise ValueError(f"Unsupported search provider: {provider}")

    async def _search_serper(self, query: str, api_key: str, num: int, **kwargs) -> Dict[str, Any]:
        """Search using Serper API."""
        headers = {
            'X-API-KEY': api_key,
            'Content-Type': 'application/json'
        }

        payload = {
            'q': query,
            'num': num,
            **kwargs  # gl, hl, type, etc.
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.search_providers['serper'],
                json=payload,
                headers=headers,
                timeout=30.0
            )
            response.raise_for_status()
            return response.json()