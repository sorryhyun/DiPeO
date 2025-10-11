"""Unified data extraction utilities for diagram formats."""

from __future__ import annotations

from typing import Any

from ..person_extractor import PersonExtractor


class DiagramDataExtractor:
    """Extract and normalize data structures from different diagram formats."""

    @staticmethod
    def extract_handles(data: dict[str, Any], format_type: str = "readable") -> dict[str, Any]:
        """Extract and normalize handles dictionary from any format.

        Args:
            data: The diagram data dictionary
            format_type: The diagram format type ('light' or 'readable')

        Returns:
            Dictionary of handles with handle IDs as keys
        """
        handles = data.get("handles", {} if format_type == "light" else {})

        if isinstance(handles, list):
            return {h.get("id", f"handle_{i}"): h for i, h in enumerate(handles)}

        return handles if isinstance(handles, dict) else {}

    @staticmethod
    def extract_persons(data: dict[str, Any], format_type: str = "readable") -> dict[str, Any]:
        """Extract persons with format-specific handling.

        Args:
            data: The diagram data dictionary
            format_type: The diagram format type ('light' or 'readable')

        Returns:
            Dictionary of persons with person IDs as keys
        """
        is_light_format = format_type == "light"
        default_value = {} if is_light_format else []
        persons_data = data.get("persons", default_value)

        if is_light_format:
            if isinstance(persons_data, dict):
                return PersonExtractor.extract_from_dict(persons_data, is_light_format=True)
            return {}
        else:
            if isinstance(persons_data, list):
                return PersonExtractor.extract_from_list(persons_data)
            elif isinstance(persons_data, dict):
                return persons_data
            return {}

    @staticmethod
    def normalize_to_dict(
        data: list | dict | None, id_key: str = "id", prefix: str = "obj"
    ) -> dict[str, Any]:
        """General list-or-dict coercion utility.

        Converts a list or dictionary to a normalized dictionary format.

        Args:
            data: List, dict, or None to normalize
            id_key: Key to use for extracting IDs from list items
            prefix: Prefix for auto-generated IDs

        Returns:
            Normalized dictionary
        """
        if isinstance(data, dict):
            return dict(data)

        if isinstance(data, list | tuple):
            return {
                (
                    item.get(id_key)
                    if isinstance(item, dict) and id_key in item
                    else f"{prefix}_{i}"
                ): item
                for i, item in enumerate(data)
            }

        return {}
