from __future__ import annotations

import logging
from typing import Any

from dipeo.models import DomainDiagram

from dipeo.domain.diagram.utils import _JsonMixin, build_node
from .base_strategy import BaseConversionStrategy

log = logging.getLogger(__name__)


class NativeJsonStrategy(_JsonMixin, BaseConversionStrategy):
    """Canonical domain JSON."""

    format_id = "native"
    format_info = {
        "name": "Domain JSON",
        "description": "Canonical format for diagram structure and execution",
        "extension": ".json",
        "supports_import": True,
        "supports_export": True,
    }

    # ---- extraction ------------------------------------------------------- #
    def _get_raw_nodes(self, data: dict[str, Any]) -> list[Any]:
        """Get nodes from native format (dict of dicts)."""
        nodes_raw = data.get("nodes", {})

        # Handle both dict and list formats
        if isinstance(nodes_raw, dict):
            # Dictionary format where keys are node IDs
            result = []
            for nid, ndata in nodes_raw.items():
                if isinstance(ndata, dict):
                    result.append((nid, ndata))
                else:
                    # Skip non-dict node data
                    continue
            return result
        elif isinstance(nodes_raw, list):
            # List format - extract nodes properly
            result = []
            for node in nodes_raw:
                if isinstance(node, dict) and "id" in node:
                    node_id = node["id"]
                    # Create node data without the id field
                    node_data = {k: v for k, v in node.items() if k != "id"}
                    result.append((node_id, node_data))
            return result
        else:
            return []

    def _process_node(self, node_data: Any, index: int) -> dict[str, Any] | None:
        """Process native format node data."""
        # Ensure node_data is a tuple
        if not isinstance(node_data, tuple) or len(node_data) != 2:
            return None

        nid, ndata = node_data

        # Ensure ndata is a dict
        if not isinstance(ndata, dict):
            return None

        return build_node(
            id=nid,
            type_=ndata.get("type", "job"),
            pos=ndata.get("position", {}),
            **ndata.get("data", {}),
        )

    # ---- export ----------------------------------------------------------- #
    def build_export_data(self, diagram: DomainDiagram) -> dict[str, Any]:
        # Export as arrays (matching frontend format) instead of dictionaries
        return {
            "nodes": [
                {
                    "id": n.id,
                    "type": n.type,
                    "position": n.position.model_dump(),
                    "data": n.data,
                }
                for n in diagram.nodes
            ],
            "handles": [h.model_dump(by_alias=True) for h in diagram.handles],
            "arrows": [
                {
                    "id": a.id,
                    "source": a.source,
                    "target": a.target,
                    "data": a.data,
                    **(
                        {
                            "content_type": a.content_type.value
                            if hasattr(a.content_type, "value")
                            else str(a.content_type)
                        }
                        if a.content_type
                        else {}
                    ),
                    **({"label": a.label} if a.label else {}),
                }
                for a in diagram.arrows
            ],
            "persons": [p.model_dump(by_alias=True) for p in diagram.persons],
            "metadata": diagram.metadata.model_dump(by_alias=True) if diagram.metadata else None,
        }

    # ---- heuristics ------------------------------------------------------- #
    def detect_confidence(self, data: dict[str, Any]) -> float:
        return 0.95 if {"nodes", "arrows"}.issubset(data) else 0.1

    def quick_match(self, content: str) -> bool:
        return content.lstrip().startswith("{") and '"nodes"' in content
