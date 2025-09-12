"""Generate GraphQL enum definitions from TypeScript enum definitions."""

import ast
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from projects.codegen.code.core.utils import parse_dipeo_output


@dataclass
class EnumValue:
    """Represents a single enum value."""
    name: str
    value: str

@dataclass
class EnumData:
    """Data for a GraphQL enum type."""
    name: str
    values: list[EnumValue]
    description: str = ""

def _normalize_enums_format(enums_raw: Any) -> dict[str, Any]:
    """Convert different enum formats to a normalized dict format."""
    enums = {}

    if isinstance(enums_raw, list):
        # New format: array of enum objects with name and members
        for enum_obj in enums_raw:
            if isinstance(enum_obj, dict) and 'name' in enum_obj:
                enums[enum_obj['name']] = enum_obj.get('members', [])
    elif isinstance(enums_raw, dict):
        # Old format: dict mapping enum names to values
        enums = enums_raw

    return enums


def _process_dict_enum_values(enum_values: dict[str, Any], enum_data: EnumData) -> None:
    """Process enum values in dictionary format."""
    for value_name, value in enum_values.items():
        # Handle different enum value formats
        if isinstance(value, str):
            enum_data.values.append(EnumValue(
                name=value_name.upper().replace('-', '_'),
                value=value
            ))
        else:
            # Default to using the key as the value
            enum_data.values.append(EnumValue(
                name=value_name.upper().replace('-', '_'),
                value=value_name.lower()
            ))


def _process_list_enum_values(enum_values: list[Any], enum_data: EnumData) -> None:
    """Process enum values in list format."""
    for value in enum_values:
        # Handle string enum members
        if isinstance(value, str):
            enum_data.values.append(EnumValue(
                name=value.upper().replace('-', '_'),
                value=value.lower()
            ))
        elif isinstance(value, dict) and 'name' in value:
            enum_data.values.append(EnumValue(
                name=value['name'].upper().replace('-', '_'),
                value=value.get('value', value['name'].lower())
            ))


def _get_enum_descriptions() -> dict[str, str]:
    """Get predefined descriptions for known enums."""
    return {
        'NodeType': 'All available node types in DiPeO diagrams',
        'Status': 'Execution and event-related status enumerations',
        'DiagramFormat': 'Diagram format enumeration',
        'LLMService': 'Available LLM service providers',
        'APIServiceType': 'API service types for external integrations',
        'DataType': 'Data type and structure enumerations',
        'ContentType': 'Content type enumerations for data handling',
        'HandleDirection': 'Direction of connection handles',
        'HandleLabel': 'Label types for connection handles',
        'MemoryView': 'Memory view types for conversation memory',
        'ExecutionMode': 'Execution mode for diagram execution',
    }


def _apply_enum_descriptions(enums_data: list[EnumData]) -> None:
    """Apply predefined descriptions to enum data."""
    descriptions = _get_enum_descriptions()
    for enum_data in enums_data:
        if enum_data.name in descriptions:
            enum_data.description = descriptions[enum_data.name]


def generate_graphql_enums(ast_cache: dict[str, Any]) -> dict[str, Any]:
    """Generate GraphQL enums from TypeScript enum definitions."""
    enums_data = []

    # Look for enum definitions in the AST cache
    for _file_path, ast_data in ast_cache.items():
        # Skip non-dict entries
        if not isinstance(ast_data, dict):
            continue

        # Check if enums is a list (new format) or dict (old format)
        enums_raw = ast_data.get('enums', [])
        enums = _normalize_enums_format(enums_raw)

        for enum_name, enum_values in enums.items():
            # Skip certain enums that don't need GraphQL versions
            if enum_name in ['EnvelopeFormat', 'SerializationFormat']:
                continue

            enum_data = EnumData(
                name=enum_name,
                description=f"{enum_name} enum values",
                values=[]
            )

            # Process enum values based on their format
            if isinstance(enum_values, dict):
                _process_dict_enum_values(enum_values, enum_data)
            elif isinstance(enum_values, list):
                _process_list_enum_values(enum_values, enum_data)

            if enum_data.values:
                enums_data.append(enum_data)

    # Apply descriptions for known enums
    _apply_enum_descriptions(enums_data)

    return {
        'enums_data': enums_data
    }

def _process_direct_glob_inputs(inputs: dict[str, Any], logger) -> dict[str, Any]:
    """Process inputs when files are passed directly as glob results."""
    ast_cache = {}

    for filepath, ast_content in inputs.items():
        # Skip special keys
        if filepath in ['inputs', 'node_id', 'globals', 'default']:
            continue

        # Parse AST content if it's a string
        ast_content = parse_dipeo_output(ast_content)
        if not isinstance(ast_content, dict):
            logger.debug(f"Could not parse AST content for {filepath}")
            continue

        # Add to cache
        if isinstance(ast_content, dict):
            ast_cache[filepath] = ast_content

    return ast_cache


def _parse_string_input(data: str, logger) -> dict:
    """Parse string input trying both JSON and literal eval."""
    result = parse_dipeo_output(data)
    return result if isinstance(result, dict) else {}


def _process_default_input(data, logger) -> dict[str, Any]:
    """Process data from 'default' key in inputs."""
    ast_cache = {}

    # Handle string input - parse it first
    if isinstance(data, str):
        data = _parse_string_input(data, logger)

    # Now data should be a dict of file paths to AST content (from glob)
    if isinstance(data, dict):
        # Check if this looks like glob results (has .json file paths as keys)
        has_json_keys = any(k.endswith('.json') for k in data if isinstance(k, str))

        if has_json_keys:
            # This is the glob result - keys are file paths, values are AST data
            ast_cache = data  # Use it directly as the cache
        else:
            # Some other dict format, try to process entries
            for filepath, ast_content in data.items():
                # Skip special keys
                if filepath in ['inputs', 'node_id', 'globals']:
                    continue

                # Parse AST content if it's a string
                ast_content = parse_dipeo_output(ast_content)
                if not isinstance(ast_content, dict):
                    logger.debug(f"Could not parse AST content for {filepath}")
                    continue

                # Add to cache
                if isinstance(ast_content, dict):
                    ast_cache[filepath] = ast_content
    elif isinstance(data, list):
        # Build cache from list
        for i, item in enumerate(data):
            if isinstance(item, dict):
                ast_cache[f"file_{i}"] = item

    return ast_cache


def _fallback_to_filesystem(logger) -> dict[str, Any]:
    """Fallback to reading AST files from filesystem."""
    logger.debug("No enum data from inputs, trying filesystem fallback")
    ast_cache = {}

    base_dir = Path(os.getenv("DIPEO_BASE_DIR", str(Path.cwd())))
    temp_dir = base_dir / "temp" / "core" / "enums"

    if temp_dir.exists():
        for ast_file in temp_dir.glob("*.ts.json"):
            with ast_file.open() as f:
                ast_cache[str(ast_file)] = json.load(f)

    return ast_cache


def _build_ast_cache(inputs: dict[str, Any], logger) -> dict[str, Any]:
    """Build AST cache from various input formats."""
    # Check if we have file paths as keys (glob result format)
    has_json_files = any(key.endswith('.json') for key in inputs)

    if has_json_files:
        # Direct glob results - process them
        return _process_direct_glob_inputs(inputs, logger)

    # Try multiple input formats as fallback
    # Check for 'default' key (DB node might wrap glob results in default)
    elif "default" in inputs:
        return _process_default_input(inputs["default"], logger)

    # Direct list input
    elif isinstance(inputs, list):
        ast_cache = {}
        for i, item in enumerate(inputs):
            if isinstance(item, dict):
                ast_cache[f"file_{i}"] = item
        return ast_cache

    # Fallback to filesystem if no data
    return _fallback_to_filesystem(logger)


def main(inputs: dict[str, Any]) -> dict[str, Any]:
    """Main entry point for GraphQL enum generation.

    Reads TypeScript AST files and generates GraphQL enum definitions.
    """
    import logging
    from datetime import datetime

    logger = logging.getLogger(__name__)
    # logger.debug(f"Received inputs keys: {list(inputs.keys())}")
    # logger.debug(f"Inputs type: {type(inputs)}")

    # Log the structure to understand what we're getting
    if "default" in inputs:
        default_value = inputs["default"]
        if isinstance(default_value, dict):
            logger.debug(f"default is dict with keys: {list(default_value.keys())[:10]}")
        elif isinstance(default_value, str):
            logger.debug(f"default is string of length {len(default_value)}, starts with: {default_value[:100]}")
        else:
            logger.debug(f"default is type: {type(default_value)}")

    # Build AST cache from inputs
    ast_cache = _build_ast_cache(inputs, logger)

    # Generate enums
    result = generate_graphql_enums(ast_cache)

    # Add metadata
    result['generation_time'] = datetime.now().isoformat()
    result['total_count'] = len(result.get('enums_data', []))

    return result
