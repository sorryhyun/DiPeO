"""Common utilities for diagram conversion strategies."""

from __future__ import annotations

import logging
from typing import Any

from dipeo.models import (
    HandleDirection,
    HandleLabel,
    NodeID,
    DataType,
    ContentType,
    create_handle_id,
    MemoryView,
)

log = logging.getLogger(__name__)


class NodeFieldMapper:
    """Maps node fields between different formats and node types."""
    
    @staticmethod
    def map_import_fields(node_type: str, props: dict[str, Any]) -> dict[str, Any]:
        """Map fields during import based on node type."""
        if node_type == "start":
            props.setdefault("custom_data", {})
            props.setdefault("output_data_structure", {})
        elif node_type == "endpoint":
            if "file_path" in props and "file_name" not in props:
                props["file_name"] = props.pop("file_path")
        elif node_type == "job":
            if "code" in props:
                node_type = "code_job"
                if "code_type" in props:
                    props["language"] = props.pop("code_type")
        elif node_type == "code_job":
            # Map old field names to new ones
            if "code_type" in props and "language" not in props:
                props["language"] = props.pop("code_type")
            # Keep both code and filePath as separate fields
            # Don't map code to filePath - they are different fields
        elif node_type == "db":
            if "source_details" in props and "file" not in props:
                props["file"] = props.pop("source_details")
        elif node_type == "person_job":
            if "memory_config" in props:
                props.pop("memory_config")
            
            if "memory_profile" in props:
                profile_str = props.get("memory_profile")
                profile_to_settings = {
                    "FULL": {
                        "view": MemoryView.all_messages,
                        "max_messages": None,
                        "preserve_system": True
                    },
                    "FOCUSED": {
                        "view": MemoryView.conversation_pairs,
                        "max_messages": 20,
                        "preserve_system": True
                    },
                    "MINIMAL": {
                        "view": MemoryView.system_and_me,
                        "max_messages": 5,
                        "preserve_system": True
                    },
                    "GOLDFISH": {
                        "view": MemoryView.conversation_pairs,
                        "max_messages": 2,
                        "preserve_system": False
                    }
                }
                
                if profile_str in profile_to_settings:
                    props["memory_settings"] = profile_to_settings[profile_str]
                    log.debug(f"Converted memory_profile '{profile_str}' to memory_settings")
        
        return props
    
    @staticmethod
    def map_export_fields(node_type: str, props: dict[str, Any]) -> dict[str, Any]:
        """Map fields during export based on node type."""
        if node_type == "endpoint" and "file_name" in props:
            props["file_path"] = props.pop("file_name")
        elif node_type == "code_job":
            # Map field names for light format compatibility if needed
            if "language" in props and "code_type" not in props:
                props["code_type"] = props["language"]
            # Keep both code and filePath as they are - don't map between them
            # Keep functionName as is - it's a new field
        elif node_type == "db" and "file" in props:
            props["source_details"] = props.pop("file")
        elif node_type == "person_job":
            if "memory_config" in props:
                props.pop("memory_config")
            if "memory_profile" in props and "memory_settings" in props:
                props.pop("memory_settings")
        
        return props


class HandleParser:
    """Parses and creates handle references."""
    
    @staticmethod
    def parse_label_with_handle(
        label_raw: str, 
        label2id: dict[str, str]
    ) -> tuple[str | None, str | None, str]:
        """Parse a label that may contain a handle suffix.
        
        Returns: (node_id, handle_name, node_label)
        """
        label = label_raw
        handle_from_split = None
        
        if label_raw not in label2id and "_" in label_raw:
            parts = label_raw.split("_")
            
            # Check for labels with spaces by replacing underscores
            for i in range(len(parts) - 1, 0, -1):
                # Try with underscores
                potential_label = "_".join(parts[:i])
                if potential_label in label2id:
                    label = potential_label
                    handle_from_split = "_".join(parts[i:])
                    break
                
                # Try with spaces instead of underscores
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
        default: str = "default"
    ) -> str:
        """Determine the handle name from split or arrow data."""
        if handle_from_split:
            # Convert "_first" to "first" for proper HandleLabel enum mapping
            if handle_from_split == "_first":
                return "first"
            return handle_from_split
        elif is_source and arrow_data and "branch" in arrow_data:
            # For condition nodes, use branch data
            branch_value = arrow_data.get("branch")
            return (
                "condtrue" if branch_value == "true"
                else "condfalse" if branch_value == "false"
                else default
            )
        else:
            return default
    
    @staticmethod
    def create_handle_ids(
        source_node_id: str,
        target_node_id: str,
        source_handle: str = "default",
        target_handle: str = "default"
    ) -> tuple[str, str]:
        """Create proper handle IDs for source and target."""
        try:
            src_handle_enum = HandleLabel(source_handle)
        except ValueError:
            src_handle_enum = HandleLabel.default
            
        try:
            dst_handle_enum = HandleLabel(target_handle)
        except ValueError:
            dst_handle_enum = HandleLabel.default
            
        source_handle_id = create_handle_id(
            NodeID(source_node_id), 
            src_handle_enum, 
            HandleDirection.output
        )
        target_handle_id = create_handle_id(
            NodeID(target_node_id), 
            dst_handle_enum, 
            HandleDirection.input
        )
        
        return source_handle_id, target_handle_id
    
    @staticmethod
    def ensure_handle_exists(
        handle_ref: str,
        direction: HandleDirection,
        nodes_dict: dict[str, Any],
        handles_dict: dict[str, Any],
        arrow: dict[str, Any]
    ) -> None:
        """Ensure a handle exists, creating it if necessary."""
        # Check if it's already a full handle ID
        parts = handle_ref.split("_")
        if len(parts) >= 3 and parts[-1] in ["input", "output"]:
            return
        
        # Parse light format handle reference
        node_id = None
        handle_name = "default"
        
        # Try to match against node labels
        for nid, node in nodes_dict.items():
            node_label = node.get("data", {}).get("label", nid) if "data" in node else nid
            for possible_handle in ["first", "default", "condtrue", "condfalse"]:
                if handle_ref == f"{node_label}_{possible_handle}":
                    node_id = nid
                    handle_name = possible_handle
                    break
            if node_id:
                break
        
        # Fall back to simple split
        if not node_id:
            parts = handle_ref.rsplit("_", 1)
            if len(parts) == 2:
                node_label_or_id, handle_name = parts
                node_id = next(
                    (nid for nid, node in nodes_dict.items() 
                     if nid == node_label_or_id or 
                     ("data" in node and node["data"].get("label") == node_label_or_id)),
                    node_label_or_id
                )
            else:
                node_id = handle_ref
                handle_name = "default"
        
        # Validate and create handle if needed
        if handle_name in ["input", "output"]:
            handle_name = "default"
        
        try:
            handle_label = HandleLabel(handle_name)
        except ValueError:
            handle_label = handle_name
        
        # Find actual node ID (case-insensitive)
        actual_node_id = next(
            (n_id for n_id in nodes_dict if n_id.lower() == node_id.lower()), 
            node_id
        )
        
        expected_handle_id = create_handle_id(actual_node_id, handle_label, direction)
        
        if expected_handle_id not in handles_dict:
            # Create the handle
            handles_dict[expected_handle_id] = {
                "id": expected_handle_id,
                "node_id": actual_node_id,
                "label": str(handle_label),
                "direction": direction.value,
                "data_type": DataType.any.value,
                "position": "right" if direction == HandleDirection.output else "left",
            }
        
        # Update arrow to use the correct handle ID
        if direction == HandleDirection.output:
            arrow["source"] = expected_handle_id
        else:
            arrow["target"] = expected_handle_id


class PersonExtractor:
    """Extracts person data from different formats."""
    
    @staticmethod
    def extract_from_dict(persons_data: dict[str, Any], is_light_format: bool = False) -> dict[str, Any]:
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
            
            if is_light_format:
                # In light format, the key is the label
                person_id = person_config.get("id", f"person_{person_key.replace(' ', '_')}")
                person_dict = {
                    "id": person_id,
                    "label": person_key,
                    "type": "person",
                    "llm_config": llm_config,
                }
            else:
                # Regular format
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
        """Extract persons from list format (readable)."""
        persons_dict = {}
        
        for person_item in persons_data:
            if isinstance(person_item, dict):
                # Each item should have one key (the person name)
                for person_name, person_config in person_item.items():
                    llm_config = {
                        "service": person_config.get("service", "openai"),
                        "model": person_config.get("model", "gpt-4-mini"),
                        "api_key_id": person_config.get("api_key_id", "default"),
                    }
                    if "system_prompt" in person_config:
                        llm_config["system_prompt"] = person_config["system_prompt"]
                    
                    # Generate a consistent person ID
                    person_id = f"person_{person_name}"
                    
                    person_dict = {
                        "id": person_id,
                        "label": person_name,
                        "type": "person",
                        "llm_config": llm_config,
                    }
                    persons_dict[person_id] = person_dict
        
        return persons_dict


class ArrowDataProcessor:
    """Processes arrow data for import/export."""
    
    @staticmethod
    def build_arrow_dict(
        arrow_id: str,
        source_handle_id: str,
        target_handle_id: str,
        arrow_data: dict[str, Any] | None = None,
        content_type: str | None = None,
        label: str | None = None
    ) -> dict[str, Any]:
        """Build a standard arrow dictionary."""
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
        
        # Set default content type if not specified
        if "content_type" not in arrow_dict and arrow_dict.get("content_type") is None:
            arrow_dict["content_type"] = ContentType.raw_text.value
        
        return arrow_dict
    
    @staticmethod
    def should_include_branch_data(source_handle: str, arrow_data: dict[str, Any]) -> bool:
        """Determine if branch data should be included in arrow data."""
        # Skip 'branch' if the handle name already contains the branch info
        return (
            "branch" in arrow_data and 
            source_handle not in ["condtrue", "condfalse"]
        )


def process_dotted_keys(props: dict[str, Any]) -> dict[str, Any]:
    """Convert dot notation keys to nested dictionaries."""
    dotted_keys = [k for k in props if '.' in k]
    for key in dotted_keys:
        value = props.pop(key)
        parts = key.split('.')
        current = props
        for part in parts[:-1]:
            if part not in current:
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value
    return props