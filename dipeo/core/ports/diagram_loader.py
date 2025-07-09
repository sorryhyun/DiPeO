"""Diagram Loader port interface."""

from typing import TYPE_CHECKING, Any, Dict, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from dipeo.models import Diagram, DiagramFormat


@runtime_checkable
class DiagramLoaderPort(Protocol):
    """Port for diagram loading and format detection.
    
    This interface defines the contract for loading diagrams from various sources
    and detecting their format (JSON, YAML, etc.).
    """

    def detect_format(self, content: str) -> "DiagramFormat":
        """Detect the format of diagram content.
        
        Args:
            content: Raw content to analyze
            
        Returns:
            Detected diagram format
            
        Raises:
            ValueError: If format cannot be detected
        """
        ...

    def load_diagram(
        self,
        content: str,
        format: Optional["DiagramFormat"] = None,
    ) -> "Diagram":
        """Load a diagram from content.
        
        Args:
            content: Raw content to parse
            format: Optional format hint. If not provided, will auto-detect
            
        Returns:
            Parsed diagram object
            
        Raises:
            ValueError: If diagram cannot be parsed
        """
        ...

    async def load_from_file(
        self,
        file_path: str,
        format: Optional["DiagramFormat"] = None,
    ) -> "Diagram":
        """Load a diagram from a file.
        
        Args:
            file_path: Path to the diagram file
            format: Optional format hint. If not provided, will auto-detect
            
        Returns:
            Parsed diagram object
            
        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If diagram cannot be parsed
        """
        ...

    def prepare_diagram(
        self,
        diagram_ref: str | Dict[str, Any] | "Diagram",
    ) -> "Diagram":
        """Prepare a diagram from various input types.
        
        Args:
            diagram_ref: Can be:
                - A file path (string)
                - A diagram dict
                - A Diagram object
                
        Returns:
            Prepared diagram object
            
        Raises:
            ValueError: If diagram cannot be prepared
        """
        ...