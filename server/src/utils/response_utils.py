
from typing import Any, Dict
from fastapi.responses import JSONResponse

from ..exceptions import AgentDiagramException


class ResponseFormatter:
    """Standardize API responses."""
    
    @staticmethod
    def success(data: Any = None, message: str = None) -> Dict[str, Any]:
        """Format successful response."""
        response = {"success": True}
        if data is not None:
            response["data"] = data
        if message:
            response["message"] = message
        return response
    
    @staticmethod
    def error(message: str, details: Dict[str, Any] = None, status_code: int = 400) -> JSONResponse:
        """Format error response."""
        content = {
            "success": False,
            "error": message
        }
        if details:
            content["details"] = details
            
        return JSONResponse(
            status_code=status_code,
            content=content
        )
    
    @staticmethod
    def paginated(items: list, total: int, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
        """Format paginated response."""
        return {
            "items": items,
            "pagination": {
                "total": total,
                "page": page,
                "per_page": per_page,
                "pages": (total + per_page - 1) // per_page
            }
        }


def handle_service_exceptions(func):
    """Decorator to handle common service exceptions."""
    async def wrapper(*args, **kwargs):
        try:
            return await func(*args, **kwargs)
        except AgentDiagramException:
            raise
        except Exception as e:
            raise AgentDiagramException(f"Unexpected error in {func.__name__}: {str(e)}")
    
    return wrapper