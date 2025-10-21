"""Unified handle operations for diagram processing.

This module consolidates handle-related functionality from handle_parser.py and handle_utils.py
into a single, well-organized module with clear separation of concerns.

Handle ID Formats:
    - Internal format: "nodeId_label_direction" (e.g., "node_123_default_output")
      Used for storage and internal operations
    - User-facing format: "label_handle" (e.g., "MyNode_condtrue")
      Used in light diagram connections
"""

from __future__ import annotations

import logging
from typing import Any, NamedTuple

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import (
    DataType,
    HandleDirection,
    HandleID,
    HandleLabel,
    NodeID,
)

logger = get_module_logger(__name__)


class ParsedHandle(NamedTuple):
    """Parsed handle components from internal handle ID format."""

    node_id: NodeID
    handle_label: HandleLabel
    direction: HandleDirection


class HandleIdOperations:
    """Operations for internal handle ID format: nodeId_label_direction.

    This class handles parsing and creation of internal handle IDs used for
    storage and internal diagram operations.
    """

    @staticmethod
    def create_handle_id(
        node_id: NodeID, handle_label: HandleLabel, direction: HandleDirection
    ) -> HandleID:
        """Create a handle ID from node ID, handle label, and direction.

        Format: [nodeId]_[handleLabel]_[direction]
        Example: create_handle_id("node_123", HandleLabel.DEFAULT, HandleDirection.OUTPUT)
                 -> "node_123_default_output"
        """
        return HandleID(f"{node_id}_{handle_label.value}_{direction.value}")

    @staticmethod
    def parse_handle_id(handle_id: HandleID) -> tuple[NodeID, HandleLabel, HandleDirection]:
        """Parse a handle ID into its components.

        Format: [nodeId]_[handleLabel]_[direction]
        Example: 'node_123_default_output' -> ('node_123', HandleLabel.DEFAULT, HandleDirection.OUTPUT)

        Raises:
            ValueError: If handle ID format is invalid
        """
        parts = handle_id.split("_")
        if len(parts) < 3:
            raise ValueError(
                f"Invalid handle ID format: {handle_id}. Expected format: nodeId_handleLabel_direction"
            )

        direction_str = parts[-1]
        handle_label_str = parts[-2]
        node_id_parts = parts[:-2]
        node_id = "_".join(node_id_parts)

        if not node_id:
            raise ValueError(f"Invalid handle ID format: {handle_id}. Node ID cannot be empty")

        try:
            direction = HandleDirection(direction_str)
        except ValueError as e:
            raise ValueError(
                f"Invalid direction '{direction_str}' in handle ID: {handle_id}"
            ) from e

        try:
            handle_label = HandleLabel(handle_label_str)
        except ValueError:
            handle_label = HandleLabel(handle_label_str)

        return NodeID(node_id), handle_label, direction

    @staticmethod
    def parse_handle_id_safe(handle_id: HandleID) -> ParsedHandle | None:
        """Parse handle ID safely, return None if invalid."""
        try:
            node_id, handle_label, direction = HandleIdOperations.parse_handle_id(handle_id)
            return ParsedHandle(node_id, handle_label, direction)
        except ValueError:
            return None

    @staticmethod
    def extract_node_id_from_handle(handle_id: HandleID) -> NodeID | None:
        """Extract just the node ID from a handle ID.

        Returns None if the handle ID is invalid.
        Example: 'node_123_default_output' -> 'node_123'
        """
        parsed = HandleIdOperations.parse_handle_id_safe(handle_id)
        return parsed.node_id if parsed else None

    @staticmethod
    def is_valid_handle_id(handle_id: str) -> bool:
        """Check if a string is a valid handle ID."""
        return HandleIdOperations.parse_handle_id_safe(HandleID(handle_id)) is not None

    @staticmethod
    def create_handle_ids(
        source_node_id: str,
        target_node_id: str,
        source_handle: str = "default",
        target_handle: str = "default",
    ) -> tuple[str, str]:
        """Create handle IDs for source and target nodes.

        Converts string handle labels to enum values and creates full handle IDs.
        """
        try:
            src_handle_enum = HandleLabel(source_handle)
        except ValueError:
            src_handle_enum = HandleLabel.DEFAULT

        try:
            dst_handle_enum = HandleLabel(target_handle)
        except ValueError:
            dst_handle_enum = HandleLabel.DEFAULT

        source_handle_id = HandleIdOperations.create_handle_id(
            NodeID(source_node_id), src_handle_enum, HandleDirection.OUTPUT
        )
        target_handle_id = HandleIdOperations.create_handle_id(
            NodeID(target_node_id), dst_handle_enum, HandleDirection.INPUT
        )

        return source_handle_id, target_handle_id


class HandleReference:
    """Handle reference with cached parsed components for performance.

    This class provides efficient access to handle components by parsing
    the handle ID once and caching the results. Use this for frequently
    accessed handles in hot paths like edge traversal.
    """

    _cache: dict[HandleID, HandleReference] = {}

    def __init__(self, handle_id: HandleID):
        """Initialize with cached parsing."""
        self.handle_id = handle_id
        self._parsed: ParsedHandle | None = None
        self._parse_error: str | None = None
        self._ensure_parsed()

    def _ensure_parsed(self) -> None:
        """Parse handle ID if needed."""
        if self._parsed is None and self._parse_error is None:
            try:
                node_id, handle_label, direction = HandleIdOperations.parse_handle_id(
                    self.handle_id
                )
                self._parsed = ParsedHandle(node_id, handle_label, direction)
            except ValueError as e:
                self._parse_error = str(e)

    @property
    def node_id(self) -> NodeID:
        """Get node ID."""
        if self._parsed:
            return self._parsed.node_id
        raise ValueError(f"Invalid handle ID: {self._parse_error}")

    @property
    def handle_label(self) -> HandleLabel:
        """Get handle label."""
        if self._parsed:
            return self._parsed.handle_label
        raise ValueError(f"Invalid handle ID: {self._parse_error}")

    @property
    def direction(self) -> HandleDirection:
        """Get direction."""
        if self._parsed:
            return self._parsed.direction
        raise ValueError(f"Invalid handle ID: {self._parse_error}")

    @property
    def is_valid(self) -> bool:
        """Check if valid."""
        return self._parsed is not None

    @classmethod
    def get_or_create(cls, handle_id: HandleID) -> HandleReference:
        """Get cached handle reference or create new one."""
        if handle_id not in cls._cache:
            cls._cache[handle_id] = cls(handle_id)
        return cls._cache[handle_id]

    @classmethod
    def clear_cache(cls) -> None:
        """Clear the handle reference cache."""
        cls._cache.clear()


class HandleLabelParser:
    """Parser for user-facing label_handle format used in light diagrams.

    This format is used in connection strings like "NodeA_condtrue -> NodeB"
    or "NodeA[condtrue] -> NodeB" (bracket syntax).
    Supports both underscore suffix format and bracket format.
    """

    @staticmethod
    def parse_bracket_syntax(
        label_raw: str, label2id: dict[str, str]
    ) -> tuple[str | None, str | None, str] | None:
        """Parse bracket syntax like 'NodeLabel[handle]'.

        Args:
            label_raw: Raw label string with bracket syntax (e.g., "MyNode[condtrue]")
            label2id: Mapping from node labels to node IDs

        Returns:
            Tuple of (node_id, handle_name, node_label) if bracket syntax detected,
            None otherwise:
            - node_id: The ID of the referenced node (None if not found)
            - handle_name: The extracted handle name from brackets
            - node_label: The node label portion (before brackets)
        """
        import re

        bracket_pattern = r"^(.+?)\[([^\]]+)\]$"
        match = re.match(bracket_pattern, label_raw.strip())

        if not match:
            return None

        node_label = match.group(1).strip()
        handle_name = match.group(2).strip()

        node_id = label2id.get(node_label)

        return node_id, handle_name, node_label

    @staticmethod
    def parse_label_with_handle(
        label_raw: str, label2id: dict[str, str]
    ) -> tuple[str | None, str | None, str]:
        """Parse a label that may contain a handle suffix or bracket notation.

        Supports both formats:
        1. Bracket syntax: "NodeLabel[handle]" (preferred, explicit)
        2. Underscore suffix: "NodeLabel_handle" (legacy, backward compatible)

        Tries bracket syntax first, then falls back to underscore splitting.

        Args:
            label_raw: Raw label string, possibly with handle (e.g., "MyNode[condtrue]" or "MyNode_condtrue")
            label2id: Mapping from node labels to node IDs

        Returns:
            Tuple of (node_id, handle_name, node_label):
            - node_id: The ID of the referenced node (None if not found)
            - handle_name: The extracted handle name (None if no handle specified)
            - node_label: The node label portion
        """
        bracket_result = HandleLabelParser.parse_bracket_syntax(label_raw, label2id)
        if bracket_result is not None:
            return bracket_result

        label = label_raw
        handle_from_split = None

        if label_raw not in label2id and "_" in label_raw:
            parts = label_raw.split("_")

            for i in range(len(parts) - 1, 0, -1):
                potential_label = "_".join(parts[:i])
                if potential_label in label2id:
                    label = potential_label
                    handle_from_split = "_".join(parts[i:])
                    break

                potential_label_with_spaces = " ".join(parts[:i])
                if potential_label_with_spaces in label2id:
                    label = potential_label_with_spaces
                    handle_from_split = "_".join(parts[i:])
                    break

        node_id = label2id.get(label)
        return node_id, handle_from_split, label

    @staticmethod
    def determine_handle_name(
        handle_from_split: str | None,
        arrow_data: dict[str, Any] | None = None,
        is_source: bool = True,
        default: str = "default",
    ) -> str:
        """Determine the handle name from parsed split or arrow data.

        Priority:
        1. Handle from split (e.g., "_first" becomes "first")
        2. Branch data for source handles (maps "true"/"false" to "condtrue"/"condfalse")
        3. Default handle

        Args:
            handle_from_split: Handle suffix extracted from label parsing
            arrow_data: Arrow/connection data that may contain branch info
            is_source: Whether this is for a source handle
            default: Default handle name if nothing else applies

        Returns:
            The determined handle name
        """
        if handle_from_split:
            if handle_from_split == "_first":
                return "first"
            return handle_from_split
        elif is_source and arrow_data and "branch" in arrow_data:
            branch_value = arrow_data.get("branch")
            return (
                "condtrue"
                if branch_value == "true"
                else "condfalse"
                if branch_value == "false"
                else default
            )
        else:
            return default


class HandleValidator:
    """Validates and ensures handle existence in diagram structures."""

    @staticmethod
    def validate_bracket_syntax_handle(
        node_label: str,
        handle_name: str,
        node_type: str,
        direction: str,
    ) -> None:
        """Validate that a handle exists in HANDLE_SPECS for bracket syntax references.

        When using bracket syntax (e.g., "NodeLabel[handle]"), this performs strict
        validation to ensure the handle exists for the node's type.

        Args:
            node_label: The node label being referenced
            handle_name: The handle name from bracket syntax
            node_type: The type of the node
            direction: "input" or "output" - the direction we're validating

        Raises:
            ValueError: If the handle doesn't exist for this node type and direction
        """
        from dipeo.diagram_generated import HandleDirection, HandleLabel
        from dipeo.domain.diagram.utils.shared_components import DEFAULT_HANDLES, HANDLE_SPECS

        handle_specs = HANDLE_SPECS.get(node_type, DEFAULT_HANDLES)

        direction_enum = HandleDirection.INPUT if direction == "input" else HandleDirection.OUTPUT

        try:
            handle_label = HandleLabel(handle_name)
        except ValueError:
            available_handles = [
                spec.label.value for spec in handle_specs if spec.direction == direction_enum
            ]
            raise ValueError(
                f"Invalid handle '{handle_name}' for node '{node_label}' of type '{node_type}'. "
                f"Available {direction} handles: {available_handles}. "
                f"Valid handle labels: {[label.value for label in HandleLabel]}"
            ) from None

        matching_specs = [
            spec
            for spec in handle_specs
            if spec.label == handle_label and spec.direction == direction_enum
        ]

        if not matching_specs:
            available_handles = [
                spec.label.value for spec in handle_specs if spec.direction == direction_enum
            ]
            raise ValueError(
                f"Handle '{handle_name}' does not exist as {direction} handle "
                f"for node '{node_label}' of type '{node_type}'. "
                f"Available {direction} handles: {available_handles}"
            )

    @staticmethod
    def ensure_handle_exists(
        handle_ref: str,
        direction: HandleDirection,
        nodes_dict: dict[str, Any],
        handles_dict: dict[str, Any],
        arrow: dict[str, Any],
    ) -> None:
        """Ensure handle exists in handles_dict, creating if needed.

        This method resolves handle references to actual handle IDs and creates
        missing handles. It updates the arrow dict with the resolved handle ID.

        Args:
            handle_ref: Handle reference (may be label_handle format or handle ID)
            direction: Handle direction (INPUT or OUTPUT)
            nodes_dict: Dictionary of nodes by ID
            handles_dict: Dictionary of handles by ID (will be modified)
            arrow: Arrow dict that will be updated with resolved handle ID
        """
        parts = handle_ref.split("_")
        if len(parts) >= 3 and parts[-1] in ["input", "output"]:
            return

        node_id, handle_name = HandleValidator._resolve_handle_reference(handle_ref, nodes_dict)

        if handle_name in ["input", "output"]:
            handle_name = "default"

        try:
            handle_label = HandleLabel(handle_name)
        except ValueError:
            handle_label = HandleLabel.DEFAULT

        actual_node_id = next(
            (n_id for n_id in nodes_dict if n_id.lower() == node_id.lower()), node_id
        )

        expected_handle_id = HandleIdOperations.create_handle_id(
            NodeID(actual_node_id), handle_label, direction
        )

        if expected_handle_id not in handles_dict:
            logger.debug(
                f"Creating handle: handle_ref={handle_ref}, handle_name={handle_name}, "
                f"handle_label={handle_label}, type={type(handle_label)}"
            )
            handles_dict[expected_handle_id] = {
                "id": expected_handle_id,
                "node_id": actual_node_id,
                "label": handle_label.value,
                "direction": direction.value,
                "data_type": DataType.ANY.value,
                "position": "right" if direction == HandleDirection.OUTPUT else "left",
            }

        if direction == HandleDirection.OUTPUT:
            arrow["source"] = expected_handle_id
        else:
            arrow["target"] = expected_handle_id

    @staticmethod
    def _resolve_handle_reference(handle_ref: str, nodes_dict: dict[str, Any]) -> tuple[str, str]:
        """Resolve handle reference to node ID and handle name.

        Tries multiple strategies to find the referenced node:
        1. Exact match with known handle suffixes
        2. Split on last underscore and match
        3. Direct node ID match

        Returns:
            Tuple of (node_id, handle_name)
        """
        node_id = None
        handle_name = "default"

        for nid, node in nodes_dict.items():
            node_label = node.get("data", {}).get("label", nid) if "data" in node else nid
            for possible_handle in ["first", "default", "condtrue", "condfalse"]:
                if handle_ref == f"{node_label}_{possible_handle}":
                    node_id = nid
                    handle_name = possible_handle
                    break
            if node_id:
                break

        if not node_id:
            parts = handle_ref.rsplit("_", 1)
            if len(parts) == 2:
                node_label_or_id, handle_name = parts
                node_id = next(
                    (
                        nid
                        for nid, node in nodes_dict.items()
                        if nid == node_label_or_id
                        or ("data" in node and node["data"].get("label") == node_label_or_id)
                    ),
                    node_label_or_id,
                )
            else:
                node_id = handle_ref
                handle_name = "default"

        return node_id, handle_name


__all__ = [
    "HandleIdOperations",
    "HandleLabelParser",
    "HandleReference",
    "HandleValidator",
    "ParsedHandle",
]
