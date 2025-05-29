
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
from pathlib import Path

from ..exceptions import ValidationError
from ...config import BASE_DIR


class BaseService(ABC):
    """Base service class with common functionality."""
    
    def __init__(self):
        pass
    
    def validate_required_fields(self, data: Dict[str, Any], required_fields: list[str]) -> None:
        """Validate that all required fields are present."""
        missing_fields = [field for field in required_fields if not data.get(field)]
        if missing_fields:
            raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")
    
    def validate_file_path(self, file_path: str, allowed_base: Path = BASE_DIR) -> Path:
        """Validate file path for security."""
        rel_path = Path(file_path)
        full_path = (allowed_base / rel_path).resolve()
        
        if allowed_base not in full_path.parents and full_path != allowed_base:
            raise ValidationError(f"Access to {full_path} is forbidden")
        
        return full_path
    
    def normalize_service_name(self, service: str) -> str:
        """Normalize service name to lowercase."""
        return (service or "chatgpt").lower()
    
    def safe_get_nested(self, obj: Any, path: str, default: Any = None) -> Any:
        """Safely get nested value from object using dot notation."""
        if obj is None:
            return default
        
        current = obj
        parts = path.split('.')
        
        try:
            for part in parts:
                if isinstance(current, dict):
                    current = current.get(part, default)
                else:
                    current = getattr(current, part, default)
                    
                if current is None:
                    return default
                    
            return current
        except (KeyError, AttributeError):
            return default