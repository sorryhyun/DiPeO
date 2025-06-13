"""
Middleware to add deprecation warnings to REST endpoints.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Callable
import logging

logger = logging.getLogger(__name__)

# Endpoints that have been migrated to GraphQL
DEPRECATED_ENDPOINTS = {
    # Diagram endpoints
    "/api/diagrams": "Use GraphQL query { diagrams { id name } }",
    "/api/diagrams/save": "Use GraphQL mutation saveDiagram",
    "/api/diagrams/convert": "Use GraphQL mutation convertDiagram", 
    "/api/diagrams/health": "Use GraphQL query { health { status } }",
    "/api/diagrams/executions": "Use GraphQL query { executions { id status } }",
    "/api/diagrams/execution-capabilities": "Use GraphQL query { executionCapabilities }",
    
    # API Keys endpoints
    "/api/api-keys": "Use GraphQL query { persons { apiKeys { id } } }",
    "/api/api-keys/test": "Use GraphQL mutation testApiKey",
    
    # Files endpoints
    "/api/files/upload": "Use GraphQL mutation uploadFile",
    
    # Conversations endpoints
    "/api/conversations": "Use GraphQL query { conversations }",
    "/api/conversations/clear": "Use GraphQL mutation clearConversations",
    
    # Models endpoints
    "/api/models/initialize": "Use GraphQL mutation initializeModel",
    "/api/import-yaml": "Use GraphQL mutation importYamlDiagram",
}


class DeprecationMiddleware(BaseHTTPMiddleware):
    """Add deprecation headers to migrated REST endpoints."""
    
    async def dispatch(self, request: Request, call_next: Callable) -> JSONResponse:
        response = await call_next(request)
        
        # Check if this is a deprecated endpoint
        path = request.url.path
        
        # Handle path parameters (e.g., /api/diagrams/{diagram_id})
        base_path = path
        for pattern in DEPRECATED_ENDPOINTS:
            if path.startswith(pattern):
                base_path = pattern
                break
        
        if base_path in DEPRECATED_ENDPOINTS:
            # Add deprecation headers
            response.headers["X-Deprecated"] = "true"
            response.headers["X-Deprecation-Message"] = DEPRECATED_ENDPOINTS[base_path]
            response.headers["Sunset"] = "2025-02-01"  # RFC 8594 Sunset header
            
            # Log deprecation warning
            logger.warning(
                f"Deprecated REST endpoint accessed: {request.method} {path}. "
                f"Alternative: {DEPRECATED_ENDPOINTS[base_path]}"
            )
        
        return response