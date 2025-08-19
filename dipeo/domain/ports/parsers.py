"""Parser ports for AST parsing of various programming languages."""

from typing import Any, Protocol


class ASTParserPort(Protocol):
    """Protocol for AST parsers supporting multiple programming languages."""
    
    async def parse(
        self,
        source: str,
        extract_patterns: list[str],
        options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Parse source code and extract AST information.
        
        Args:
            source: The source code to parse
            extract_patterns: List of patterns to extract (e.g., ["interface", "type", "enum"])
            options: Optional parser-specific options
                
        Returns:
            Dictionary containing:
                - ast: The extracted AST nodes organized by pattern type
                - metadata: Additional metadata about the parsing operation
        """
        ...
    
    async def parse_file(
        self,
        file_path: str,
        extract_patterns: list[str],
        options: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """Parse a file and extract AST information.
        
        Args:
            file_path: Path to the file to parse
            extract_patterns: List of patterns to extract
            options: Optional parser-specific options
            
        Returns:
            Dictionary containing extracted AST and metadata
        """
        ...
    
    async def parse_batch(
        self,
        sources: dict[str, str],
        extract_patterns: list[str],
        options: dict[str, Any] | None = None
    ) -> dict[str, dict[str, Any]]:
        """Parse multiple source code strings in batch.
        
        Args:
            sources: Dictionary mapping keys to source code
            extract_patterns: List of patterns to extract
            options: Optional parser-specific options
            
        Returns:
            Dictionary mapping each key to its parse result
        """
        ...