
from typing import Optional


class ArrowUtils:
    """Utility for arrow source/target extraction."""
    
    @staticmethod
    def get_source(arrow: dict) -> Optional[str]:
        """Extract source node ID from arrow."""
        return arrow.get("source")
    
    @staticmethod
    def get_target(arrow: dict) -> Optional[str]:
        """Extract target node ID from arrow."""
        return arrow.get("target")
    
    @staticmethod
    def get_id(arrow: dict) -> Optional[str]:
        """Extract arrow ID."""
        return arrow.get("id")
    
    @staticmethod
    def get_arrow_kind(arrow: dict) -> Optional[str]:
        """Extract arrow kind/type from arrow data."""
        return arrow.get("data", {}).get("arrowKind")
    
    @staticmethod
    def get_content_type(arrow: dict) -> Optional[str]:
        """Extract content type from arrow data."""
        return arrow.get("data", {}).get("contentType")
    
    @staticmethod
    def get_content(arrow: dict) -> Optional[str]:
        """Extract content from arrow data."""
        return arrow.get("data", {}).get("content")
    
    @staticmethod
    def get_variable_list(arrow: dict) -> list:
        """Extract variable list from arrow data."""
        return arrow.get("data", {}).get("variableList", [])
    
    @staticmethod
    def is_first_only(arrow: dict) -> bool:
        """Check if arrow is configured for first-only execution."""
        return arrow.get("data", {}).get("arrowKind") == "fixed"