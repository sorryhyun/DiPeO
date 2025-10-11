"""Unified arrow building and ID generation utilities."""

from __future__ import annotations

from typing import Any

from dipeo.diagram_generated import ContentType, HandleDirection, HandleLabel, NodeID

from .handle_operations import HandleIdOperations

__all__ = (
    "ArrowBuilder",
    "ArrowIdGenerator",
    "arrows_list_to_dict",
    "create_arrow_dict",
)


class ArrowIdGenerator:
    """Generates arrow IDs using different strategies."""

    @staticmethod
    def from_handles(source_handle: str, target_handle: str) -> str:
        """Generate arrow ID from handle IDs: 'source->target'."""
        return f"{source_handle}->{target_handle}"

    @staticmethod
    def from_index(index: int, prefix: str = "arrow") -> str:
        """Generate arrow ID from index: 'arrow_{index}'."""
        return f"{prefix}_{index}"

    @staticmethod
    def from_connection(source_node: str, target_node: str, index: int) -> str:
        """Generate arrow ID from connection: '{source}_to_{target}_{index}'."""
        return f"{source_node}_to_{target_node}_{index}"


class ArrowBuilder:
    """Builds arrows and arrow components for diagrams."""

    @staticmethod
    def create_arrow_id(source_handle: str, target_handle: str) -> str:
        """Create arrow ID from source and target handle IDs.

        This is an alias for ArrowIdGenerator.from_handles() for backward compatibility.
        """
        return ArrowIdGenerator.from_handles(source_handle, target_handle)

    @staticmethod
    def create_simple_arrow(
        source_node: str,
        target_node: str,
        source_label: HandleLabel = HandleLabel.DEFAULT,
        target_label: HandleLabel = HandleLabel.DEFAULT,
    ) -> tuple[str, str, str]:
        """Create a simple arrow between two nodes.

        Args:
            source_node: Source node ID
            target_node: Target node ID
            source_label: Source handle label (default: DEFAULT)
            target_label: Target handle label (default: DEFAULT)

        Returns:
            Tuple of (arrow_id, source_handle_id, target_handle_id)
        """
        source_handle_id = str(
            HandleIdOperations.create_handle_id(
                NodeID(source_node), source_label, HandleDirection.OUTPUT
            )
        )
        target_handle_id = str(
            HandleIdOperations.create_handle_id(
                NodeID(target_node), target_label, HandleDirection.INPUT
            )
        )
        arrow_id = ArrowBuilder.create_arrow_id(source_handle_id, target_handle_id)
        return arrow_id, source_handle_id, target_handle_id


def arrows_list_to_dict(arrows_list: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    """Convert a list of arrows to a dictionary indexed by arrow ID.

    This is useful for converting light format arrow lists to the dictionary format
    used internally.

    Args:
        arrows_list: List of arrow dictionaries, each with an 'id' key

    Returns:
        Dictionary mapping arrow IDs to arrow dictionaries
    """
    return {arrow["id"]: arrow for arrow in arrows_list}


def create_arrow_dict(
    arrow_id: str,
    source_handle_id: str,
    target_handle_id: str,
    arrow_data: dict[str, Any] | None = None,
    content_type: str | None = None,
    label: str | None = None,
) -> dict[str, Any]:
    """Build a complete arrow dictionary from components.

    This function creates a fully-formed arrow dictionary suitable for use in
    diagram compilation. It handles optional fields and sets default content type.

    Args:
        arrow_id: Unique identifier for the arrow
        source_handle_id: ID of the source handle
        target_handle_id: ID of the target handle
        arrow_data: Optional data payload for the arrow
        content_type: Optional content type (defaults to RAW_TEXT)
        label: Optional label for the arrow

    Returns:
        Dictionary with arrow properties
    """
    arrow_dict: dict[str, Any] = {
        "id": arrow_id,
        "source": source_handle_id,
        "target": target_handle_id,
    }

    if arrow_data:
        arrow_dict["data"] = arrow_data

    if content_type:
        arrow_dict["content_type"] = content_type

    if label:
        arrow_dict["label"] = label

    if "content_type" not in arrow_dict or arrow_dict.get("content_type") is None:
        arrow_dict["content_type"] = ContentType.RAW_TEXT

    return arrow_dict
