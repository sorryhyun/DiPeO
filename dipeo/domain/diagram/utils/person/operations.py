"""Person operations - extraction and reference resolution.

This module provides utilities for:
- Extracting person data from different diagram formats (dict/list)
- Resolving person references between ID and label forms
- Converting person references in node data structures
"""

from __future__ import annotations

from typing import Any


class PersonExtractor:
    """Extracts person data from different formats."""

    @staticmethod
    def extract_from_dict(
        persons_data: dict[str, Any], is_light_format: bool = False
    ) -> dict[str, Any]:
        """Extract persons from dictionary format.

        Args:
            persons_data: Dictionary of person configurations
            is_light_format: Whether this is light format (affects ID/label mapping)

        Returns:
            Dictionary of person data keyed by person ID
        """
        persons_dict = {}

        for person_key, person_config in persons_data.items():
            llm_config = {
                "service": person_config.get("service", "openai"),
                "model": person_config.get("model", "gpt-4-mini"),
                "api_key_id": person_config.get("api_key_id", "default"),
            }
            if "system_prompt" in person_config:
                llm_config["system_prompt"] = person_config["system_prompt"]
            if "prompt_file" in person_config:
                llm_config["prompt_file"] = person_config["prompt_file"]

            if is_light_format:
                person_id = person_config.get("id", person_key)
                person_dict = {
                    "id": person_id,
                    "label": person_key,
                    "type": "person",
                    "llm_config": llm_config,
                }
            else:
                person_id = person_key
                person_dict = {
                    "id": person_id,
                    "label": person_config.get("label", person_key),
                    "type": "person",
                    "llm_config": llm_config,
                }

            persons_dict[person_id] = person_dict

        return persons_dict

    @staticmethod
    def extract_from_list(persons_data: list[Any]) -> dict[str, Any]:
        """Extract persons from list format (readable or native array).

        Args:
            persons_data: List of person configurations

        Returns:
            Dictionary of person data keyed by person ID
        """
        persons_dict = {}

        for person_item in persons_data:
            if isinstance(person_item, dict):
                if "id" in person_item and "llm_config" in person_item:
                    person_id = person_item["id"]
                    persons_dict[person_id] = person_item
                else:
                    # Readable format with person name as key
                    for person_name, person_config in person_item.items():
                        llm_config = {
                            "service": person_config.get("service", "openai"),
                            "model": person_config.get("model", "gpt-4-mini"),
                            "api_key_id": person_config.get("api_key_id", "default"),
                        }
                        if "system_prompt" in person_config:
                            llm_config["system_prompt"] = person_config["system_prompt"]
                        if "prompt_file" in person_config:
                            llm_config["prompt_file"] = person_config["prompt_file"]

                        person_id = f"person_{person_name}"

                        person_dict = {
                            "id": person_id,
                            "label": person_name,
                            "type": "person",
                            "llm_config": llm_config,
                        }
                        persons_dict[person_id] = person_dict

        return persons_dict


class PersonReferenceResolver:
    """Resolve person references between ID and label forms.

    Handles bidirectional conversion:
    - label → ID (during diagram deserialization)
    - ID → label (during diagram serialization)
    """

    @staticmethod
    def build_label_to_id_map(persons_dict: dict[str, Any]) -> dict[str, str]:
        """Build mapping from person labels to person IDs.

        Args:
            persons_dict: Dictionary of person data keyed by person ID

        Returns:
            Dictionary mapping person labels to person IDs
        """
        label_to_id = {}
        if persons_dict:
            for person_id, person_data in persons_dict.items():
                label = person_data.get("label", person_id)
                label_to_id[label] = person_id
        return label_to_id

    @staticmethod
    def build_id_to_label_map(persons: list[Any]) -> dict[str, str]:
        """Build mapping from person IDs to person labels.

        Args:
            persons: List of person objects with id and label attributes

        Returns:
            Dictionary mapping person IDs to person labels
        """
        id_to_label = {}
        for person in persons:
            id_to_label[person.id] = person.label
        return id_to_label

    @staticmethod
    def resolve_person_in_node(
        node: dict[str, Any], mapping: dict[str, str], node_type_filter: str = "person_job"
    ) -> None:
        """Convert person references in a node using the provided mapping.

        Modifies the node in-place, converting person references found in:
        - node["person"]
        - node["props"]["person"]
        - node["data"]["person"]

        Args:
            node: The node dictionary to modify
            mapping: Dictionary mapping old reference to new reference
            node_type_filter: Only process nodes of this type (default: "person_job")
        """
        if node.get("type") != node_type_filter:
            return

        locations = [
            ("person", node),
            ("person", node.get("props", {}))
            if isinstance(node.get("props"), dict)
            else (None, None),
            ("person", node.get("data", {}))
            if isinstance(node.get("data"), dict)
            else (None, None),
        ]

        for key, container in locations:
            if key and container is not None and key in container:
                person_ref = container[key]
                if person_ref in mapping:
                    container[key] = mapping[person_ref]

    @staticmethod
    def resolve_persons_in_nodes(
        nodes_dict: dict[str, dict[str, Any]],
        mapping: dict[str, str],
        node_type_filter: str = "person_job",
    ) -> None:
        """Convert person references in all nodes using the provided mapping.

        Args:
            nodes_dict: Dictionary of nodes keyed by node ID
            mapping: Dictionary mapping old reference to new reference
            node_type_filter: Only process nodes of this type (default: "person_job")
        """
        if not mapping:
            return

        for node in nodes_dict.values():
            PersonReferenceResolver.resolve_person_in_node(node, mapping, node_type_filter)
