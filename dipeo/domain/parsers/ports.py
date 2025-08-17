"""Protocol definition for AST parsers."""

from typing import Protocol, Dict, Any, List, Optional, runtime_checkable


@runtime_checkable
class ASTParserPort(Protocol):
    
    async def parse(
        self,
        source: str,
        extract_patterns: List[str],
        options: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        ...