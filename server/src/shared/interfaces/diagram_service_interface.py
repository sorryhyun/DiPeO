"""Interface for diagram service."""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from src.shared.domain import DiagramID


class IDiagramService(ABC):
    """Interface for handling diagram operations."""
    
    @abstractmethod
    def import_yaml(self, yaml_text: str) -> dict:
        """Import YAML agent definitions and convert to diagram state."""
        pass
    
    @abstractmethod
    def export_llm_yaml(self, diagram: dict) -> str:
        """Export diagram state to LLM-friendly YAML format."""
        pass
    
    @abstractmethod
    def list_diagram_files(self, directory: Optional[str] = None) -> List[Dict[str, Any]]:
        """List diagram files in the specified directory."""
        pass
    
    @abstractmethod
    def load_diagram(self, path: str) -> Dict[str, Any]:
        """Load a diagram from disk."""
        pass
    
    @abstractmethod
    def save_diagram(self, path: str, diagram: Dict[str, Any]) -> None:
        """Save a diagram to disk."""
        pass
    
    @abstractmethod
    def create_diagram(self, name: str, diagram: Dict[str, Any], format: str = 'json') -> str:
        """Create a new diagram file."""
        pass
    
    @abstractmethod
    def update_diagram(self, path: str, diagram: Dict[str, Any]) -> None:
        """Update an existing diagram file."""
        pass
    
    @abstractmethod
    def delete_diagram(self, path: str) -> None:
        """Delete a diagram file."""
        pass
    
    @abstractmethod
    async def save_diagram_with_id(self, diagram_dict: Dict[str, Any], filename: str) -> str:
        """Save diagram with a generated ID."""
        pass
    
    @abstractmethod
    async def get_diagram(self, diagram_id: DiagramID) -> Optional[Dict[str, Any]]:
        """Get diagram by ID."""
        pass