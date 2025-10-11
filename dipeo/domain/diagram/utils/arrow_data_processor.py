"""Processes arrow data for import/export."""

from __future__ import annotations

from typing import Any

from dipeo.diagram_generated import ContentType


class ArrowDataProcessor:
    """Processes arrow data for import/export."""

    @staticmethod
    def build_arrow_dict(
        arrow_id: str,
        source_handle_id: str,
        target_handle_id: str,
        arrow_data: dict[str, Any] | None = None,
        content_type: str | None = None,
        label: str | None = None,
    ) -> dict[str, Any]:
        """Build arrow dictionary."""
        arrow_dict = {
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

        if "content_type" not in arrow_dict and arrow_dict.get("content_type") is None:
            arrow_dict["content_type"] = ContentType.RAW_TEXT

        return arrow_dict

    @staticmethod
    def should_include_branch_data(source_handle: str, arrow_data: dict[str, Any]) -> bool:
        """Check if branch data should be included."""
        return "branch" in arrow_data and source_handle not in ["condtrue", "condfalse"]
