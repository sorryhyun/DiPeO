"""Base conversion strategy with common logic for all diagram formats."""

from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from typing import Any

from dipeo.models import DomainDiagram

from dipeo.core.ports import FormatStrategy
from dipeo.domain.diagram.utils import (
    extract_common_arrows,
    dict_to_domain_diagram,
    PersonExtractor,
    ArrowDataProcessor,
    HandleParser,
    NodeFieldMapper,
    process_dotted_keys,
)

log = logging.getLogger(__name__)


class BaseConversionStrategy(FormatStrategy, ABC):
    """Template Method pattern for diagram conversion with customizable node/arrow extraction."""

    def extract_nodes(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        raw_nodes = self._get_raw_nodes(data)
        nodes = []
        
        for idx, node_data in enumerate(raw_nodes):
            node = self._process_node(node_data, idx)
            if node:
                nodes.append(node)
        
        return nodes
    
    @abstractmethod
    def _get_raw_nodes(self, data: dict[str, Any]) -> list[Any]:
        pass
    
    @abstractmethod
    def _process_node(self, node_data: Any, index: int) -> dict[str, Any] | None:
        pass
    
    def _extract_node_props(self, node_data: dict[str, Any]) -> dict[str, Any]:
        props = self._get_node_base_props(node_data)
        
        props = process_dotted_keys(props)
        
        node_type = node_data.get("type", "job")
        props = NodeFieldMapper.map_import_fields(node_type, props)
        
        return props
    
    def _get_node_base_props(self, node_data: dict[str, Any]) -> dict[str, Any]:
        exclude_fields = {"id", "type", "position", "label"}
        return {k: v for k, v in node_data.items() if k not in exclude_fields}
    

    def extract_arrows(
        self, data: dict[str, Any], nodes: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Default implementation for dict-based formats. Override for label-based formats."""
        return extract_common_arrows(data.get("arrows", []))
    

    def build_export_data(self, diagram: DomainDiagram) -> dict[str, Any]:
        """Override entire method for custom formats, or specific _export_* methods."""
        result = {}
        
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
        nodes = {}
        for n in diagram.nodes:
            node_type = str(n.type).split(".")[-1]
            
            data = NodeFieldMapper.map_export_fields(node_type, n.data.copy())
            
            nodes[n.id] = {
                "type": node_type,
                "position": n.position.model_dump(),
                "data": data,
            }
        return nodes
    
    def _export_arrows(self, diagram: DomainDiagram) -> Any:
        return {
            a.id: self._format_arrow(a)
            for a in diagram.arrows
        }
    
    def _format_arrow(self, arrow: Any) -> dict[str, Any]:
        return ArrowDataProcessor.build_arrow_dict(
            arrow.id,
            arrow.source,
            arrow.target,
            arrow.data,
            arrow.content_type.value if hasattr(arrow.content_type, "value") else str(arrow.content_type) if hasattr(arrow, 'content_type') and arrow.content_type else None,
            arrow.label if hasattr(arrow, 'label') else None
        )
    
    def _export_handles(self, diagram: DomainDiagram) -> Any:
        return {h.id: h.model_dump(by_alias=True) for h in diagram.handles}
    
    def _export_persons(self, diagram: DomainDiagram) -> Any:
        return {p.id: p.model_dump(by_alias=True) for p in diagram.persons}
    
    def _export_metadata(self, diagram: DomainDiagram) -> Any:
        return diagram.metadata.model_dump(by_alias=True) if diagram.metadata else None
    
    
    def _create_node_id(self, index: int, prefix: str = "node") -> str:
        return f"{prefix}_{index}"
    
    def _parse_position(self, position_data: Any) -> dict[str, float]:
        if isinstance(position_data, dict):
            return position_data
        return {}
    
    def _filter_node_properties(self, props: dict[str, Any], node_type: str) -> dict[str, Any]:
        return {
            k: v
            for k, v in props.items()
            if v not in (None, "", {}, [])
        }
    
    
    def detect_confidence(self, data: dict[str, Any]) -> float:
        return 0.5
    
    def quick_match(self, content: str) -> bool:
        """Should be overridden for better performance."""
        try:
            self.parse(content)
            return True
        except Exception:
            return False
    
    
    def deserialize_to_domain(self, content: str) -> DomainDiagram:
        """Subclasses should override for format-specific logic."""
        data = self.parse(content)
        
        data = self._clean_graphql_fields(data)
        
        nodes_list = self.extract_nodes(data)
        nodes_dict = self._build_nodes_dict(nodes_list)
        
        arrows_list = self.extract_arrows(data, nodes_list)
        arrows_dict = self._build_arrows_dict(arrows_list)
        
        handles_dict = self._extract_handles_dict(data)
        persons_dict = self._extract_persons_dict(data)
        
        diagram_dict = {
            "nodes": nodes_dict,
            "arrows": arrows_dict,
            "handles": handles_dict,
            "persons": persons_dict,
            "metadata": data.get("metadata"),
        }
        
        diagram_dict = self._apply_format_transformations(diagram_dict, data)
        
        return dict_to_domain_diagram(diagram_dict)
    
    def serialize_from_domain(self, diagram: DomainDiagram) -> str:
        data = self.build_export_data(diagram)
        return self.format(data)
    
    
    def _build_nodes_dict(self, nodes_list: list[dict[str, Any]]) -> dict[str, Any]:
        """Override for custom node creation."""
        from dipeo.diagram_generated.conversions import node_kind_to_domain_type
        from dipeo.domain.diagram.utils.shared_components import PositionCalculator
        
        position_calculator = PositionCalculator()
        nodes_dict = {}
        
        for index, node_data in enumerate(nodes_list):
            if "id" not in node_data:
                continue
                
            node_id = node_data["id"]
            node_type_str = node_data.get("type", "person_job")
            
            try:
                node_type = node_kind_to_domain_type(node_type_str)
            except ValueError:
                log.warning(f"Unknown node type '{node_type_str}', defaulting to 'person_job'")
                node_type = node_kind_to_domain_type("person_job")
            
            position = node_data.get("position")
            if not position:
                position = position_calculator.calculate_grid_position(index)
            
            exclude_fields = {"id", "type", "position", "handles", "arrows"}
            properties = {k: v for k, v in node_data.items() if k not in exclude_fields}
            
            nodes_dict[node_id] = {
                "id": node_id,
                "type": node_type.value,
                "position": position,
                "data": properties
            }
            
        return nodes_dict
    
    def _build_arrows_dict(self, arrows_list: list[dict[str, Any]]) -> dict[str, Any]:
        """Override for custom arrow creation."""
        from dipeo.models import ContentType
        
        arrows_dict = {}
        for i, arrow_data in enumerate(arrows_list):
            arrow_id = arrow_data.get("id", f"arrow_{i}")
            
            arrow_dict = ArrowDataProcessor.build_arrow_dict(
                arrow_id,
                arrow_data.get("source", ""),
                arrow_data.get("target", ""),
                arrow_data.get("data"),
                arrow_data.get("content_type"),
                arrow_data.get("label")
            )
            
            arrows_dict[arrow_id] = arrow_dict
            
        return arrows_dict
    
    def _extract_handles_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Override for format-specific logic."""
        handles_data = data.get("handles", {})
        if isinstance(handles_data, dict):
            return handles_data
        elif isinstance(handles_data, list):
            return {
                handle.get("id", f"handle_{i}"): handle
                for i, handle in enumerate(handles_data)
            }
        return {}
    
    def _extract_persons_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Override for format-specific logic."""
        persons_data = data.get("persons", {})
        if isinstance(persons_data, dict):
            return persons_data
        elif isinstance(persons_data, list):
            return PersonExtractor.extract_from_list(persons_data)
        return {}
    
    def _apply_format_transformations(
        self, diagram_dict: dict[str, Any], original_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Override in subclasses."""
        return diagram_dict
    
    def _clean_graphql_fields(self, data: Any) -> Any:
        if isinstance(data, dict):
            return {
                k: self._clean_graphql_fields(v) 
                for k, v in data.items() 
                if not k.startswith('__')
            }
        elif isinstance(data, list):
            return [self._clean_graphql_fields(item) for item in data]
        else:
            return data