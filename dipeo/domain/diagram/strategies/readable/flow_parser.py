from __future__ import annotations

import re
from typing import Any

from dipeo.config.base_logger import get_module_logger
from dipeo.domain.diagram.models.format_models import ReadableArrow, ReadableNode
from dipeo.domain.diagram.utils import (
    ArrowDataProcessor,
    HandleParser,
)

logger = get_module_logger(__name__)


class FlowParser:
    """Parser for readable diagram flow definitions.

    Handles both old and new format flow parsing for readable diagrams.
    """

    def parse_flow_to_arrows(
        self, flow_data: list[Any], nodes: list[ReadableNode]
    ) -> list[ReadableArrow]:
        """Parse flow data into arrow connections.

        Args:
            flow_data: List of flow items from diagram
            nodes: List of nodes to connect

        Returns:
            List of ReadableArrow objects representing connections
        """
        arrows = []
        label_to_node = {node.label: node for node in nodes}
        arrow_counter = 0

        for flow_item in flow_data:
            if isinstance(flow_item, str):
                if " -> " in flow_item:
                    parts = flow_item.split(" -> ")
                    if len(parts) == 2:
                        src_label, dst_label = parts[0].strip(), parts[1].strip()
                        if src_label in label_to_node and dst_label in label_to_node:
                            arrow = ReadableArrow(
                                id=f"arrow_{arrow_counter}",
                                source=label_to_node[src_label].id,
                                target=label_to_node[dst_label].id,
                            )
                            arrows.append(arrow)
                            arrow_counter += 1
            elif isinstance(flow_item, dict):
                for src, dst_data in flow_item.items():
                    src_node, src_handle = self._parse_node_and_handle(src, label_to_node)
                    if not src_node:
                        continue

                    if isinstance(dst_data, str):
                        parsed_arrows = self._parse_flow_destination(
                            src_node, src_handle, dst_data, label_to_node, arrow_counter
                        )
                        arrows.extend(parsed_arrows)
                        arrow_counter += len(parsed_arrows)
                    elif isinstance(dst_data, list):
                        for dst in dst_data:
                            if isinstance(dst, str):
                                parsed_arrows = self._parse_flow_destination(
                                    src_node, src_handle, dst, label_to_node, arrow_counter
                                )
                                arrows.extend(parsed_arrows)
                                arrow_counter += len(parsed_arrows)

        return arrows

    def _parse_node_and_handle(
        self, node_str: str, label_to_node: dict[str, ReadableNode]
    ) -> tuple[ReadableNode | None, str]:
        """Parse a node reference that may include a handle suffix.

        Args:
            node_str: String like "NodeName_condtrue" or "NodeName"
            label_to_node: Mapping of node labels to node objects

        Returns:
            Tuple of (node, handle) or (None, "") if not found
        """
        if "_" in node_str:
            parts = node_str.rsplit("_", 1)
            base_label = parts[0]
            handle = parts[1]

            if handle in ["condtrue", "condfalse"]:
                if base_label in label_to_node:
                    return label_to_node[base_label], handle
            elif node_str in label_to_node:
                return label_to_node[node_str], "default"
            elif base_label in label_to_node:
                return label_to_node[base_label], handle

        if node_str in label_to_node:
            return label_to_node[node_str], "default"

        return None, ""

    def _parse_flow_destination(
        self,
        src_node: ReadableNode,
        src_handle: str,
        dst_str: str,
        label_to_node: dict[str, ReadableNode],
        arrow_counter: int,
    ) -> list[ReadableArrow]:
        """Parse a flow destination string into arrows.

        Handles both old and new format destinations.

        Args:
            src_node: Source node
            src_handle: Source handle name
            dst_str: Destination string to parse
            label_to_node: Node lookup map
            arrow_counter: Current arrow counter for ID generation

        Returns:
            List of arrows created from the destination
        """
        arrows = []
        dst_str = dst_str.strip()

        if self._is_new_format(dst_str):
            parsed = self._parse_new_format_flow(dst_str, label_to_node)
            if parsed:
                for dst_node, dst_handle, content_type, label, from_handle in parsed:
                    actual_src_handle = from_handle if from_handle else src_handle

                    arrow = ReadableArrow(
                        id=f"arrow_{arrow_counter}",
                        source=src_node.id,
                        target=dst_node.id,
                        source_handle=actual_src_handle if actual_src_handle != "default" else None,
                        target_handle=dst_handle if dst_handle != "default" else None,
                        label=label,
                        data={"content_type": content_type} if content_type else None,
                    )
                    arrows.append(arrow)
        else:
            parsed = self._parse_old_format_flow(dst_str, label_to_node)
            if parsed:
                dst_node, dst_handle, content_type, label = parsed
                arrow = ReadableArrow(
                    id=f"arrow_{arrow_counter}",
                    source=src_node.id,
                    target=dst_node.id,
                    source_handle=src_handle if src_handle != "default" else None,
                    target_handle=dst_handle if dst_handle != "default" else None,
                    label=label,
                    data={"content_type": content_type} if content_type else None,
                )
                arrows.append(arrow)

        return arrows

    def _is_new_format(self, dst_str: str) -> bool:
        """Detect if a flow string uses the new format.

        Args:
            dst_str: Destination string to check

        Returns:
            True if new format, False if old format
        """
        new_keywords = [' to "', ' from "', ' in "', ' as "', ' naming "']
        return any(keyword in dst_str for keyword in new_keywords)

    def _parse_new_format_flow(
        self, flow_str: str, label_to_node: dict[str, ReadableNode]
    ) -> list[tuple]:
        """Parse new format flow strings.

        New format examples:
        - to "NodeName"
        - to "NodeName" in "handleName"
        - from "sourceHandle" to "NodeName"

        Args:
            flow_str: Flow string in new format
            label_to_node: Node lookup map

        Returns:
            List of tuples (dst_node, dst_handle, content_type, label, from_handle)
        """
        results = []

        if " - to " in flow_str:
            destinations = flow_str.split(" - ")
            for dest in destinations:
                if dest.strip().startswith("to "):
                    parsed = self._parse_single_new_format(dest.strip(), label_to_node)
                    if parsed:
                        results.append(parsed)
        else:
            parsed = self._parse_single_new_format(flow_str, label_to_node)
            if parsed:
                results.append(parsed)

        return results

    def _parse_single_new_format(
        self, flow_str: str, label_to_node: dict[str, ReadableNode]
    ) -> tuple | None:
        """Parse a single new format flow entry.

        Args:
            flow_str: Single flow entry in new format
            label_to_node: Node lookup map

        Returns:
            Tuple of (dst_node, dst_handle, content_type, label, from_handle) or None
        """
        dst_node = None
        dst_handle = "default"
        content_type = None
        label = None
        from_handle = None

        from_match = re.search(r'from\s+"([^"]+)"', flow_str)
        if from_match:
            from_handle = from_match.group(1)

        to_match = re.search(r'to\s+"([^"]+)"', flow_str)
        if to_match:
            node_name = to_match.group(1)
            if node_name in label_to_node:
                dst_node = label_to_node[node_name]

        in_match = re.search(r'in\s+"([^"]+)"', flow_str)
        if in_match:
            dst_handle = in_match.group(1)

        as_match = re.search(r'as\s+"([^"]+)"', flow_str)
        if as_match:
            content_type = as_match.group(1)

        naming_match = re.search(r'naming\s+"([^"]+)"', flow_str)
        if naming_match:
            label = naming_match.group(1)

        if dst_node:
            return (dst_node, dst_handle, content_type, label, from_handle)

        return None

    def _parse_old_format_flow(
        self, dst_str: str, label_to_node: dict[str, ReadableNode]
    ) -> tuple | None:
        """Parse old format flow strings.

        Old format examples:
        - NodeName
        - NodeName_handleName
        - NodeName(label)
        - NodeName(raw_text)

        Args:
            dst_str: Destination string in old format
            label_to_node: Node lookup map

        Returns:
            Tuple of (dst_node, dst_handle, content_type, label) or None
        """
        content_type = None
        label = None
        clean_dst = dst_str

        if "(" in clean_dst and ")" in clean_dst:
            paren_matches = re.findall(r"\(([^)]+)\)", clean_dst)
            if paren_matches:
                known_types = ["raw_text", "conversation_state", "variable", "json", "object"]
                for _i, match in enumerate(paren_matches):
                    if match in known_types and not content_type:
                        content_type = match
                        clean_dst = clean_dst.replace(f"({match})", "", 1)
                    elif not label:
                        label = match
                        clean_dst = clean_dst.replace(f"({match})", "", 1)

        clean_dst = clean_dst.strip()

        dst_node, dst_handle = self._parse_node_and_handle(clean_dst, label_to_node)

        if dst_node:
            return (dst_node, dst_handle, content_type, label)

        return None

    def parse_single_flow(
        self, src: str, dst: str | bool | int, label2id: dict[str, str], idx: int
    ) -> list[dict[str, Any]]:
        """Parse a single flow connection (legacy method).

        This method appears to be legacy code but is kept for backward compatibility.

        Args:
            src: Source node label
            dst: Destination node label or value
            label2id: Mapping of labels to IDs
            idx: Arrow index

        Returns:
            List of arrow dictionaries
        """
        arrows = []

        dst_str = str(dst)

        content_type = None
        label = None
        clean_dst = dst_str.strip()

        if "(" in clean_dst:
            paren_matches = re.findall(r"\(([^)]+)\)", clean_dst)
            if paren_matches:
                known_types = ["raw_text", "conversation_state", "variable", "json", "object"]
                for match in paren_matches:
                    if match in known_types:
                        content_type = match
                        clean_dst = clean_dst.replace(f"({match})", "").strip()
                        break

        if "(" in clean_dst and ")" in clean_dst:
            start = clean_dst.find("(")
            end = clean_dst.find(")", start)
            if start != -1 and end != -1:
                label = clean_dst[start + 1 : end]
                clean_dst = clean_dst[:start].strip() + clean_dst[end + 1 :].strip()

        src_id, src_handle_from_split, src_label = HandleParser.parse_label_with_handle(
            src.strip(), label2id
        )
        dst_id, dst_handle_from_split, dst_label = HandleParser.parse_label_with_handle(
            clean_dst.strip(), label2id
        )

        src_handle = src_handle_from_split if src_handle_from_split else "default"
        dst_handle = dst_handle_from_split if dst_handle_from_split else "default"

        if src_id and dst_id:
            source_handle_id, target_handle_id = HandleParser.create_handle_ids(
                src_id, dst_id, src_handle, dst_handle
            )

            arrow_dict = ArrowDataProcessor.build_arrow_dict(
                f"arrow_{idx}",
                source_handle_id,
                target_handle_id,
                None,
                content_type,
                label,
            )

            arrows.append(arrow_dict)
        else:
            logger.warning(f"Could not find nodes for flow: {src_label} -> {dst_label}")

        return arrows
