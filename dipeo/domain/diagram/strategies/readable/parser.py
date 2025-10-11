"""Parser for readable format - handles node and connection parsing."""

from __future__ import annotations

from typing import Any

from dipeo.domain.diagram.models.format_models import ReadableDiagram, ReadableNode

from .flow_parser import FlowParser


class ReadableParser:
    """Parses raw data into ReadableDiagram structure."""

    def __init__(self):
        self.flow_parser = FlowParser()

    def parse_to_readable_diagram(self, data: dict[str, Any]) -> ReadableDiagram:
        """Parse raw data dictionary into a ReadableDiagram."""
        nodes = self._parse_nodes(data.get("nodes", []))
        arrows = self.flow_parser.parse_flow_to_arrows(data.get("flow", []), nodes)

        return ReadableDiagram(
            version="readable",
            nodes=nodes,
            arrows=arrows,
            persons=data.get("persons"),
            api_keys=data.get("api_keys"),
            metadata=data.get("metadata"),
        )

    def _parse_nodes(self, nodes_data: list) -> list[ReadableNode]:
        """Parse nodes from raw data."""
        nodes = []
        for index, node_data in enumerate(nodes_data):
            if not isinstance(node_data, dict):
                continue

            step = node_data
            ((name, cfg),) = step.items()

            position = {}
            clean_name = name
            if " @(" in name and name.endswith(")"):
                parts = name.split(" @(")
                if len(parts) == 2:
                    clean_name = parts[0]
                    pos_str = parts[1][:-1]  # Remove trailing )
                    try:
                        x, y = pos_str.split(",")
                        position = {"x": int(x.strip()), "y": int(y.strip())}
                    except (ValueError, IndexError):
                        pass

            if not position:
                position = cfg.get("position", {})

            node_type = cfg.get("type") or ("start" if index == 0 else "job")

            props = {k: v for k, v in cfg.items() if k not in {"position", "type"}}

            node = ReadableNode(
                id=self._create_node_id(index),
                type=node_type,
                label=clean_name,
                position=position if position else {"x": 0, "y": 0},
                props=props,
            )
            nodes.append(node)

        return nodes

    def _create_node_id(self, index: int, prefix: str = "node") -> str:
        """Generate a unique node ID."""
        return f"{prefix}_{index}"
