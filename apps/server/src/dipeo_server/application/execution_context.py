from dataclasses import dataclass
from typing import Any

from dipeo.application import UnifiedExecutionContext
from dipeo.models import parse_handle_id, extract_node_id_from_handle


@dataclass
class ExecutionContext(UnifiedExecutionContext):
    """Server-specific execution context extending the unified execution context.

    This adds server-specific functionality while maintaining compatibility
    with the UnifiedExecutionContext used throughout the system.
    """

    def find_edges_from(self, node_id: str) -> list[Any]:
        """Find edges originating from a node."""
        from dipeo.models import DomainArrow
        # Parse handle IDs to extract node IDs (format: nodeId_handleName_direction)
        result = []
        for edge in self.edges:
            if hasattr(edge, 'source') and edge.source:
                # Extract node ID from handle
                edge_node_id = extract_node_id_from_handle(edge.source)
                if edge_node_id == node_id:
                    result.append(edge)
        return result

    def find_edges_to(self, node_id: str) -> list[Any]:
        """Find edges targeting a node."""
        from dipeo.models import DomainArrow
        # Parse handle IDs to extract node IDs (format: nodeId_handleName_direction)
        result = []
        for edge in self.edges:
            if hasattr(edge, 'target') and edge.target:
                # Extract node ID from handle
                edge_node_id = extract_node_id_from_handle(edge.target)
                if edge_node_id == node_id:
                    result.append(edge)
        return result

