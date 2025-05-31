
from typing import Optional


class Arrow:
    """Unified arrow class with simplified logic."""
    
    def __init__(self, arrow_data: dict):
        self._data = arrow_data
        
    @property
    def source(self) -> Optional[str]:
        """Get source node ID."""
        return self._data.get("source")
        
    @property
    def target(self) -> Optional[str]:
        """Get target node ID."""
        return self._data.get("target")
        
    @property
    def id(self) -> Optional[str]:
        """Get arrow ID."""
        return self._data.get("id")
        
    @property
    def is_first_only(self) -> bool:
        """Check if arrow is configured for first-only execution."""
        return self._data.get("data", {}).get("arrowKind") == "fixed"
    
    def should_accept_input(self, node_execution_count: int) -> bool:
        """Unified first-only handle logic."""
        if self.is_first_only:
            return node_execution_count == 0
        else:
            return node_execution_count > 0 or not self.has_first_only_sibling
    
    @property
    def has_first_only_sibling(self) -> bool:
        """Check if there are other first-only arrows targeting the same node."""
        # This would need to be set externally when creating Arrow instances
        # For now, return False as a safe default
        return False


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