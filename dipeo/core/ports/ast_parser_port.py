"""Protocol definition for AST parsers."""

from typing import Protocol, Dict, Any, List, Optional, runtime_checkable


@runtime_checkable
class ASTParserPort(Protocol):
    """Protocol for AST parsers.
    
    This protocol defines the interface that all AST parsers must implement.
    It provides a consistent way to parse source code and extract AST information
    regardless of the underlying language or parser implementation.
    """
    
    async def parse(
        self,
        source: str,
        extract_patterns: List[str],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Parse source code and extract AST information.
        
        Args:
            source: The source code to parse
            extract_patterns: List of patterns to extract (e.g., ["interface", "type", "enum"])
            options: Optional parser-specific options
            
        Returns:
            Dictionary containing:
                - ast: The extracted AST nodes organized by pattern type
                - metadata: Additional metadata about the parsing operation
                
        Raises:
            ParserError: If parsing fails
        """
        ...