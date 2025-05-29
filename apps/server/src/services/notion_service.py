"""Notion API integration service."""

import httpx
from typing import Dict, Any, List, Optional
from ..exceptions import DiagramExecutionError
from ..utils.base_service import BaseService


class NotionService(BaseService):
    """Service for interacting with Notion API."""
    
    def __init__(self):
        super().__init__()
        self.base_url = "https://api.notion.com/v1"
        self.version = "2022-06-28"
    
    async def query_database(
        self,
        api_key: str,
        database_id: str,
        filter_obj: Optional[Dict[str, Any]] = None,
        sorts: Optional[List[Dict[str, Any]]] = None,
        page_size: int = 100
    ) -> Dict[str, Any]:
        """Query a Notion database."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.version
        }
        
        payload = {
            "page_size": page_size
        }
        if filter_obj:
            payload["filter"] = filter_obj
        if sorts:
            payload["sorts"] = sorts
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/databases/{database_id}/query",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise DiagramExecutionError(f"Notion API error: {e.response.text}")
            except Exception as e:
                raise DiagramExecutionError(f"Failed to query Notion database: {str(e)}")
    
    async def create_page(
        self,
        api_key: str,
        parent_database_id: str,
        properties: Dict[str, Any],
        children: Optional[List[Dict[str, Any]]] = None
    ) -> Dict[str, Any]:
        """Create a new page in a Notion database."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.version
        }
        
        payload = {
            "parent": {"database_id": parent_database_id},
            "properties": properties
        }
        if children:
            payload["children"] = children
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/pages",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise DiagramExecutionError(f"Notion API error: {e.response.text}")
            except Exception as e:
                raise DiagramExecutionError(f"Failed to create Notion page: {str(e)}")
    
    async def update_page(
        self,
        api_key: str,
        page_id: str,
        properties: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Update properties of an existing Notion page."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.version
        }
        
        payload = {"properties": properties}
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    f"{self.base_url}/pages/{page_id}",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise DiagramExecutionError(f"Notion API error: {e.response.text}")
            except Exception as e:
                raise DiagramExecutionError(f"Failed to update Notion page: {str(e)}")
    
    async def get_page(
        self,
        api_key: str,
        page_id: str
    ) -> Dict[str, Any]:
        """Get a Notion page by ID."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Notion-Version": self.version
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(
                    f"{self.base_url}/pages/{page_id}",
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise DiagramExecutionError(f"Notion API error: {e.response.text}")
            except Exception as e:
                raise DiagramExecutionError(f"Failed to get Notion page: {str(e)}")
    
    async def search(
        self,
        api_key: str,
        query: str,
        filter_obj: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Search for pages and databases."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.version
        }
        
        payload = {"query": query}
        if filter_obj:
            payload["filter"] = filter_obj
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{self.base_url}/search",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise DiagramExecutionError(f"Notion API error: {e.response.text}")
            except Exception as e:
                raise DiagramExecutionError(f"Failed to search Notion: {str(e)}")
    
    async def update_block_children(
        self,
        api_key: str,
        block_id: str,
        children: List[Dict[str, Any]],
        after: Optional[str] = None
    ) -> Dict[str, Any]:
        """Update/append children blocks to a parent block."""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Notion-Version": self.version
        }
        
        payload = {"children": children}
        if after:
            payload["after"] = after
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.patch(
                    f"{self.base_url}/blocks/{block_id}/children",
                    json=payload,
                    headers=headers,
                    timeout=30.0
                )
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                raise DiagramExecutionError(f"Notion API error: {e.response.text}")
            except Exception as e:
                raise DiagramExecutionError(f"Failed to update block children: {str(e)}")