"""Transformer for readable format - handles data transformations."""

from __future__ import annotations

from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import DomainDiagram, HandleDirection
from dipeo.domain.diagram.models.format_models import ReadableArrow, ReadableDiagram, ReadableNode
from dipeo.domain.diagram.utils import (
    DiagramDataExtractor,
    HandleIdOperations,
    NodeDictionaryBuilder,
    NodeFieldMapper,
    build_node,
    process_dotted_keys,
)

logger = get_module_logger(__name__)


class ReadableTransformer:
    """Transforms data between different representations."""

    def readable_diagram_to_dict(
        self, readable_diagram: ReadableDiagram, original_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Convert ReadableDiagram to dictionary format for DomainDiagram."""
        nodes_list = []
        for node in readable_diagram.nodes:
            props = process_dotted_keys(node.props)
            props = NodeFieldMapper.map_import_fields(node.type, props)

            node_dict = build_node(
                id=node.id, type_=node.type, pos=node.position, label=node.label, **props
            )
            nodes_list.append(node_dict)

        nodes_dict = self._build_nodes_dict(nodes_list)

        arrows_dict = {}
        for arrow in readable_diagram.arrows:
            arrows_dict[arrow.id] = {
                "id": arrow.id,
                "source": HandleIdOperations.create_handle_id(
                    arrow.source, arrow.source_handle or "default", HandleDirection.OUTPUT
                ),
                "target": HandleIdOperations.create_handle_id(
                    arrow.target, arrow.target_handle or "default", HandleDirection.INPUT
                ),
                "data": arrow.data or {},
                "label": arrow.label,
            }

        handles_dict = self._extract_handles_dict(original_data)
        persons_dict = self._extract_persons_dict(original_data)

        return {
            "nodes": nodes_dict,
            "arrows": arrows_dict,
            "handles": handles_dict,
            "persons": persons_dict,
            "metadata": readable_diagram.metadata,
        }

    def _build_nodes_dict(self, nodes_list: list[dict[str, Any]]) -> dict[str, Any]:
        """Build nodes dictionary from list of node data."""
        return NodeDictionaryBuilder.build_with_enrichment(nodes_list)

    def domain_to_readable_diagram(self, diagram: DomainDiagram) -> ReadableDiagram:
        """Convert DomainDiagram to ReadableDiagram for export."""
        nodes = []
        for n in diagram.nodes:
            node = ReadableNode(
                id=n.id,
                type=str(n.type).split(".")[-1].lower(),
                label=n.data.get("label") or n.id,
                position={"x": round(n.position.x), "y": round(n.position.y)},
                props={
                    k: v for k, v in n.data.items() if k != "label" and v not in (None, "", {}, [])
                },
            )
            nodes.append(node)

        arrows = []
        for a in diagram.arrows:
            s_node_id, s_handle, _ = HandleIdOperations.parse_handle_id(a.source)
            t_node_id, t_handle, _ = HandleIdOperations.parse_handle_id(a.target)

            arrow = ReadableArrow(
                id=a.id,
                source=s_node_id,
                target=t_node_id,
                source_handle=s_handle if s_handle != "default" else None,
                target_handle=t_handle if t_handle != "default" else None,
                label=a.label,
                data=a.data if a.data else None,
            )
            arrows.append(arrow)

        persons_data = None
        if diagram.persons:
            persons_data = []
            for p in diagram.persons:
                person_dict = {
                    "id": p.id,
                    "label": p.label,
                    "llm_config": {
                        "service": p.llm_config.service.value
                        if hasattr(p.llm_config.service, "value")
                        else str(p.llm_config.service),
                        "model": p.llm_config.model,
                        "api_key_id": p.llm_config.api_key_id,
                    },
                }
                if p.llm_config.system_prompt:
                    person_dict["llm_config"]["system_prompt"] = p.llm_config.system_prompt
                persons_data.append(person_dict)

        return ReadableDiagram(
            version="readable",
            nodes=nodes,
            arrows=arrows,
            persons=persons_data,
            metadata=diagram.metadata.model_dump(exclude_none=True) if diagram.metadata else None,
        )

    def _extract_handles_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract handles dictionary from original data."""
        return DiagramDataExtractor.extract_handles(data, format_type="readable")

    def _extract_persons_dict(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract persons dictionary from original data."""
        return DiagramDataExtractor.extract_persons(data, format_type="readable")

    def apply_format_transformations(
        self, diagram_dict: dict[str, Any], original_data: dict[str, Any]
    ) -> dict[str, Any]:
        """Apply format-specific transformations to the diagram dictionary."""
        return diagram_dict
