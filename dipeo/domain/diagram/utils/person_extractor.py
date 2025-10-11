"""Extracts person data from different formats."""

from __future__ import annotations

from typing import Any


class PersonExtractor:
    """Extracts person data from different formats."""

    @staticmethod
    def extract_from_dict(
        persons_data: dict[str, Any], is_light_format: bool = False
    ) -> dict[str, Any]:
        """Extract persons from dictionary format."""
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
                # Light format: key is label, used directly as person_id
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
        """Extract persons from list format (readable or native array)."""
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
