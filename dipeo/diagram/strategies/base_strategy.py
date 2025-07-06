"""Base conversion strategy with common logic for all diagram formats."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from dipeo.domain import DomainDiagram

from ..base import FormatStrategy
from ..shared_components import (
    build_node,
    coerce_to_dict,
    ensure_position,
    extract_common_arrows,
    PositionCalculator,
    ArrowBuilder,
)

log = logging.getLogger(__name__)


class BaseConversionStrategy(FormatStrategy, ABC):
    """Base class for diagram conversion strategies with common logic.
    
    This base class implements the Template Method pattern, providing common
    logic for node and arrow extraction while allowing subclasses to customize
    specific parts of the conversion process.
    """

    def extract_nodes(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract nodes from data with common processing logic."""
        raw_nodes = self._get_raw_nodes(data)
        nodes = []
        
        for idx, node_data in enumerate(raw_nodes):
            node = self._process_node(node_data, idx)
            if node:
                ensure_position(node, idx)
                nodes.append(node)
        
        return nodes
    
    @abstractmethod
    def _get_raw_nodes(self, data: dict[str, Any]) -> list[Any]:
        pass
    
    @abstractmethod
    def _process_node(self, node_data: Any, index: int) -> dict[str, Any] | None:
        pass
    

    def extract_arrows(
        self, data: dict[str, Any], nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Extract arrows with common processing logic.

        Default implementation uses extract_common_arrows for dict-based formats.
        Override for label-based formats.
        """
        return extract_common_arrows(data.get("arrows", []))
    

    def build_export_data(self, diagram: DomainDiagram) -> dict[str, Any]:
        """Build export data with common structure.

        Subclasses can override this method entirely for custom formats,
        or override specific _export_* methods to customize parts.
        """
        result = {}
        
        # Add each component if it has content
        nodes = self._export_nodes(diagram)
        if nodes:
            result["nodes"] = nodes
            
        arrows = self._export_arrows(diagram)
        if arrows:
            result["arrows"] = arrows
            
        handles = self._export_handles(diagram)
        if handles:
            result["handles"] = handles
            
        persons = self._export_persons(diagram)
        if persons:
            result["persons"] = persons
            
        metadata = self._export_metadata(diagram)
        if metadata:
            result["metadata"] = metadata
            
        return result
    
    def _export_nodes(self, diagram: DomainDiagram) -> Any:
        """Export nodes in format-specific structure."""
        # Default implementation for dict-based formats
        return {
            n.id: {
                "type": n.type,
                "position": n.position.model_dump(),
                "data": n.data,
            }
            for n in diagram.nodes
        }
    
    def _export_arrows(self, diagram: DomainDiagram) -> Any:
        """Export arrows in format-specific structure."""
        # Default implementation for dict-based formats
        return {
            a.id: self._format_arrow(a)
            for a in diagram.arrows
        }
    
    def _format_arrow(self, arrow: Any) -> dict[str, Any]:
        """Format a single arrow for export."""
        result = {
            "source": arrow.source,
            "target": arrow.target,
            "data": arrow.data,
        }
        
        # Add optional fields if present
        if hasattr(arrow, 'content_type') and arrow.content_type:
            result["content_type"] = (
                arrow.content_type.value 
                if hasattr(arrow.content_type, "value") 
                else str(arrow.content_type)
            )
        
        if hasattr(arrow, 'label') and arrow.label:
            result["label"] = arrow.label
            
        return result
    
    def _export_handles(self, diagram: DomainDiagram) -> Any:
        """Export handles in format-specific structure."""
        return {h.id: h.model_dump(by_alias=True) for h in diagram.handles}
    
    def _export_persons(self, diagram: DomainDiagram) -> Any:
        """Export persons in format-specific structure."""
        return {p.id: p.model_dump(by_alias=True) for p in diagram.persons}
    
    def _export_metadata(self, diagram: DomainDiagram) -> Any:
        """Export metadata in format-specific structure."""
        return diagram.metadata.model_dump(by_alias=True) if diagram.metadata else None
    
    # ---- Utility Methods -------------------------------------------------- #
    
    def _create_node_id(self, index: int, prefix: str = "node") -> str:
        """Create a node ID based on index."""
        return f"{prefix}_{index}"
    
    def _parse_position(self, position_data: Any) -> dict[str, float]:
        """Parse position data into standard format."""
        if isinstance(position_data, dict):
            return position_data
        return {}
    
    def _map_node_type_for_import(self, node_type: str, node_data: dict[str, Any]) -> str:
        """Map node type during import. Override for legacy compatibility."""
        return node_type
    
    def _map_node_type_for_export(self, node_type: str) -> str:
        """Map node type during export. Override for format-specific naming."""
        return str(node_type).split(".")[-1]
    
    def _filter_node_properties(self, props: dict[str, Any], node_type: str) -> dict[str, Any]:
        """Filter node properties for export. Override to customize."""
        return {
            k: v
            for k, v in props.items()
            if v not in (None, "", {}, [])
        }
    
    # ---- Default Implementations ------------------------------------------ #
    
    def detect_confidence(self, data: dict[str, Any]) -> float:
        """Default confidence detection - can be overridden."""
        return 0.5
    
    def quick_match(self, content: str) -> bool:
        """Default quick match - should be overridden for better performance."""
        try:
            self.parse(content)
            return True
        except Exception:
            return False