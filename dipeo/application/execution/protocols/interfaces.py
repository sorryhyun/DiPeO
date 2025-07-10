"""Interfaces for execution services to avoid circular dependencies."""

from typing import Protocol, Dict, Any, Optional
from dipeo.models import DomainArrow, NodeOutput


class ArrowProcessorProtocol(Protocol):
    """Protocol for arrow processing to avoid circular imports."""
    
    def process_arrow_delivery(
        self,
        arrow: DomainArrow,
        source_output: NodeOutput,
        target_node_type: str,
        memory_config: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Process arrow delivery with transformations."""
        ...