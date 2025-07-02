from __future__ import annotations

import logging
from typing import Any, Callable
from dipeo_domain import DomainDiagram
from .shared_components import (
    build_node,
    coerce_to_dict,
    ensure_position,
)

log = logging.getLogger(__name__)

from .conversion_utils import _JsonMixin, _BaseStrategy


class NativeJsonStrategy(_JsonMixin, _BaseStrategy):
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
    def extract_nodes(self, data: dict[str, Any]) -> list[dict[str, Any]]:  # noqa: D401
        built: list[dict[str, Any]] = []
        for idx, (nid, ndata) in enumerate(
            coerce_to_dict(data.get("nodes", {})).items()
        ):
            node = build_node(
                id=nid,
                type_=ndata.get("type", "job"),
                pos=ndata.get("position", {}),
                **ndata.get("data", {}),
            )
            ensure_position(node, idx)
            built.append(node)
        return built

    # ---- export ----------------------------------------------------------- #
    def build_export_data(self, diagram: DomainDiagram) -> dict[str, Any]:  # noqa: D401
        return {
            "nodes": {
                n.id: {
                    "type": n.type,
                    "position": n.position.model_dump(),
                    "data": n.data,
                }
                for n in diagram.nodes
            },
            "handles": {h.id: h.model_dump(by_alias=True) for h in diagram.handles},
            "arrows": {
                a.id: {
                    "source": a.source, 
                    "target": a.target, 
                    "data": a.data,
                    **({
                        "content_type": a.content_type.value if hasattr(a.content_type, "value") else str(a.content_type)
                    } if a.content_type else {}),
                    **({
                        "label": a.label
                    } if a.label else {})
                }
                for a in diagram.arrows
            },
            "persons": {p.id: p.model_dump(by_alias=True) for p in diagram.persons},
            "metadata": diagram.metadata.model_dump(by_alias=True)
            if diagram.metadata
            else None,
        }

    # ---- heuristics ------------------------------------------------------- #
    def detect_confidence(self, data: dict[str, Any]) -> float:  # noqa: D401
        return 0.95 if {"nodes", "arrows"}.issubset(data) else 0.1

    def quick_match(self, content: str) -> bool:  # noqa: D401
        return content.lstrip().startswith("{") and '"nodes"' in content

