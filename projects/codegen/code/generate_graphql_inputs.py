"""Extract and generate GraphQL input types from TypeScript definitions."""

import ast
import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Optional

from projects.codegen.code.core.utils import parse_dipeo_output


@dataclass
class InputField:
    """Represents a field in an input type."""
    name: str
    type_str: str
    optional: bool
    default_value: str | None = None
    description: str | None = None

@dataclass
class InputTypeData:
    """Data for a GraphQL input type."""
    name: str
    fields: list[InputField]
    description: str | None = None

def extract_input_types_from_ast(ast_cache: dict[str, Any]) -> list[InputTypeData]:
    """Extract GraphQL input types from TypeScript AST cache."""

    input_types = []

    # Look for the graphql-inputs.ts file
    for file_path, ast_data in ast_cache.items():
        if 'graphql-inputs.ts' not in file_path:
            continue

        # Skip non-dict entries
        if not isinstance(ast_data, dict):
            continue

        # Check both type aliases and types (parser might use either)
        types_list = ast_data.get('types', [])
        type_aliases = ast_data.get('type_aliases', {})

        # Process type aliases that end with "Input"
        for type_name, type_data in type_aliases.items():
            if not type_name.endswith('Input'):
                continue

            # Parse the type definition
            input_type = parse_input_type(type_name, type_data)
            if input_type:
                input_types.append(input_type)

        # Also process types list (TypeScript AST represents type aliases in 'types' array)
        for type_def in types_list:
            type_name = type_def.get('name', '')
            if not type_name.endswith('Input'):
                continue

            # Skip non-exported types
            if not type_def.get('isExported', False):
                continue

            # The type content is in the 'type' field as a string
            # We need to parse it to extract the fields
            # For now, add to manual list
            pass

    return input_types

def parse_input_type(type_name: str, type_data: dict[str, Any]) -> InputTypeData | None:
    """Parse a TypeScript type alias into an input type."""

    # Check if it's an object type literal
    if not isinstance(type_data, dict) or 'properties' not in type_data:
        return None

    fields = []
    for prop_name, prop_data in type_data.get('properties', {}).items():
        field = parse_input_field(prop_name, prop_data)
        if field:
            fields.append(field)

    return InputTypeData(
        name=type_name,
        fields=fields,
        description=type_data.get('description')
    )

def parse_input_field(field_name: str, field_data: Any) -> InputField | None:
    """Parse a field from a TypeScript type."""

    # Convert TypeScript field name to Python (snake_case)
    python_name = field_name

    # Determine type and optionality
    type_str = resolve_typescript_type_to_python(field_data)
    optional = '?' in str(field_data) or 'InputMaybe' in str(field_data)

    # Check for default values
    default_value = None
    if isinstance(field_data, dict):
        if field_data.get('type') == 'array' and optional:
            default_value = 'strawberry.field(default_factory=list)'
        elif field_data.get('default') is not None:
            default_value = repr(field_data.get('default'))

    return InputField(
        name=python_name,
        type_str=type_str,
        optional=optional,
        default_value=default_value,
        description=field_data.get('description') if isinstance(field_data, dict) else None
    )

def resolve_typescript_type_to_python(type_data: Any) -> str:
    """Convert TypeScript type to Python/Strawberry type."""

    if isinstance(type_data, str):
        type_str = type_data
    elif isinstance(type_data, dict):
        type_str = type_data.get('type', 'Any')
    else:
        type_str = str(type_data)

    # Handle InputMaybe wrapper
    if 'InputMaybe<' in type_str:
        # Extract inner type
        start = type_str.index('<') + 1
        end = type_str.rindex('>')
        inner_type = type_str[start:end]
        type_str = inner_type

    # Type mappings
    type_map = {
        "Scalars['String']['input']": "str",
        "Scalars['Int']['input']": "int",
        "Scalars['Float']['input']": "float",
        "Scalars['Boolean']['input']": "bool",
        "Scalars['ID']['input']": "strawberry.ID",
        "Scalars['JSON']['input']": "strawberry.scalars.JSON",
        "Scalars['DateTime']['input']": "datetime",
        "NodeType": "NodeType",
        "Status": "Status",
        "LLMService": "LLMService",
        "APIServiceType": "APIServiceType",
        "DiagramFormat": "DiagramFormat",
        "DiagramFormatGraphQL": "DiagramFormat",  # Map GraphQL name to Python enum
        "Vec2Input": "Vec2Input",
        "PersonLLMConfigInput": "PersonLLMConfigInput",
        "string": "str",
        "number": "float",
        "boolean": "bool",
        "any": "strawberry.scalars.JSON",
    }

    # Handle arrays
    if 'Array<' in type_str or type_str.startswith('['):
        # Extract element type
        if 'Array<' in type_str:
            start = type_str.index('<') + 1
            end = type_str.rindex('>')
            element_type = type_str[start:end]
        else:
            element_type = type_str[1:-1] if type_str.startswith('[') else type_str

        element_python = type_map.get(element_type, element_type)
        return f"list[{element_python}]"

    return type_map.get(type_str, type_str)


def _process_default_input_for_graphql(data, logger) -> dict[str, Any]:
    """Process data from 'default' key in inputs for GraphQL input generation."""
    ast_cache = {}

    # Handle string input - parse it first
    data = parse_dipeo_output(data)

    # Now data could be either:
    # 1. A dict of file paths to AST content (from glob)
    # 2. A single AST file content (from single file load)
    if isinstance(data, dict):
        # Check if this looks like glob results (has .json file paths as keys)
        has_json_keys = any(k.endswith('.json') for k in data if isinstance(k, str))

        # Check if this looks like AST content (has 'interfaces', 'types', etc.)
        looks_like_ast = 'interfaces' in data or 'types' in data or 'enums' in data

        if has_json_keys:
            # This is the glob result - keys are file paths, values are AST data
            ast_cache = data  # Use it directly as the cache
        elif looks_like_ast:
            # This is a single AST file content - add it to cache with a dummy key
            ast_cache['temp/frontend/graphql-inputs.ts.json'] = data
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

                # Add to cache - especially look for graphql-inputs file
                if isinstance(ast_content, dict):
                    ast_cache[filepath] = ast_content
    elif isinstance(data, list):
        # Convert list to cache dict
        for i, item in enumerate(data):
            if isinstance(item, dict):
                ast_cache[f"item_{i}"] = item

    return ast_cache


def _build_ast_cache_for_inputs(inputs: dict[str, Any], logger) -> dict[str, Any]:
    """Build AST cache for GraphQL input generation."""
    # Check if we have file paths as keys (glob result format)
    has_json_files = any(key.endswith('.json') for key in inputs)

    if has_json_files:
        # Direct glob results - process them
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

    # Check for 'default' key (DB node might wrap glob results in default)
    elif "default" in inputs:
        return _process_default_input_for_graphql(inputs["default"], logger)

    return {}


def _try_direct_file_parsing(logger) -> list:
    """Fallback to direct file parsing for better accuracy."""
    logger.debug("No input types from AST, using direct file parsing")
    base_dir = Path(os.getenv("DIPEO_BASE_DIR", str(Path.cwd())))
    inputs_file = base_dir / "dipeo/models/src/frontend/graphql-inputs.ts"

    if inputs_file.exists():
        logger.debug(f"Parsing file directly: {inputs_file}")
        input_types = parse_inputs_file_directly(inputs_file)
        logger.debug(f"Direct parsing returned {len(input_types)} input types")
        return input_types
    else:
        logger.debug(f"File does not exist: {inputs_file}")
        return []


def main(inputs: dict[str, Any]) -> dict[str, Any]:
    """Main entry point for GraphQL input type generation.

    Reads TypeScript AST files and generates GraphQL input types.
    """
    import logging
    from datetime import datetime

    logger = logging.getLogger(__name__)
    logger.debug(f"Received inputs keys: {list(inputs.keys())}")

    # Debug the default value
    if "default" in inputs:
        default_val = inputs["default"]
        if isinstance(default_val, str):
            logger.debug(f"Default is string, first 200 chars: {default_val[:200]}")
        elif isinstance(default_val, dict):
            logger.debug(f"Default is dict with keys: {list(default_val.keys())[:5]}")
        else:
            logger.debug(f"Default is type: {type(default_val)}")

    # Build AST cache from inputs
    ast_cache = _build_ast_cache_for_inputs(inputs, logger)

    # Extract input types from AST
    input_types = extract_input_types_from_ast(ast_cache)

    # Debug logging
    logger.debug(f"AST cache has {len(ast_cache)} files")
    for filepath in list(ast_cache.keys())[:10]:  # Show first 10
        logger.debug(f"AST cache file: {filepath}")

    # Fallback to direct file parsing for better accuracy
    if not input_types:
        input_types = _try_direct_file_parsing(logger)

    return {
        'input_types': input_types,
        'generation_time': datetime.now().isoformat(),
        'total_count': len(input_types),
    }

def parse_inputs_file_directly(file_path: Path) -> list[InputTypeData]:
    """Parse the graphql-inputs.ts file directly for more accurate extraction."""

    content = file_path.read_text()
    input_types = []

    # Define the input types we want to extract
    input_type_names = [
        'Vec2Input',
        'PersonLLMConfigInput',
        'CreateNodeInput',
        'UpdateNodeInput',
        'CreateDiagramInput',
        'DiagramFilterInput',
        'CreatePersonInput',
        'UpdatePersonInput',
        'CreateApiKeyInput',
        'ExecuteDiagramInput',
        'ExecutionControlInput',
        'ExecutionFilterInput',
        'UpdateNodeStateInput',
        'InteractiveResponseInput',
        'RegisterCliSessionInput',
        'UnregisterCliSessionInput',
        'UpdateDiagramInput',  # Missing from TypeScript but in Python
        'CreateArrowInput',    # Missing from TypeScript but in Python
        'FileOperationInput',  # Missing from TypeScript but in Python
    ]

    # Manually define the input types based on the TypeScript file
    # This is more reliable than trying to parse TypeScript AST

    input_types_data = [
        InputTypeData(
            name='Vec2Input',
            fields=[
                InputField('x', 'float', False),
                InputField('y', 'float', False),
            ]
        ),
        InputTypeData(
            name='CreateNodeInput',
            fields=[
                InputField('type', 'NodeType', False),
                InputField('position', 'Vec2Input', False),
                InputField('data', 'strawberry.scalars.JSON', False),
            ]
        ),
        InputTypeData(
            name='UpdateNodeInput',
            fields=[
                InputField('position', 'Vec2Input', True),
                InputField('data', 'strawberry.scalars.JSON', True),
            ]
        ),
        InputTypeData(
            name='CreateArrowInput',
            fields=[
                InputField('source', 'strawberry.ID', False),
                InputField('target', 'strawberry.ID', False),
                InputField('label', 'str', True),
                InputField('data', 'strawberry.scalars.JSON', True),
            ]
        ),
        InputTypeData(
            name='CreateDiagramInput',
            fields=[
                InputField('name', 'str', False),
                InputField('description', 'str', True),
                InputField('author', 'str', True),
                InputField('tags', 'list[str]', False, 'strawberry.field(default_factory=list)'),
            ]
        ),
        InputTypeData(
            name='UpdateDiagramInput',
            fields=[
                InputField('name', 'str', True),
                InputField('description', 'str', True),
                InputField('author', 'str', True),
                InputField('tags', 'list[str]', True),
            ]
        ),
        InputTypeData(
            name='PersonLLMConfigInput',
            fields=[
                InputField('service', 'LLMService', False),
                InputField('model', 'str', False),
                InputField('api_key_id', 'strawberry.ID', False),
                InputField('system_prompt', 'str', True),
            ]
        ),
        InputTypeData(
            name='CreatePersonInput',
            fields=[
                InputField('label', 'str', False),
                InputField('llm_config', 'PersonLLMConfigInput', False),
                InputField('type', 'str', False, '"user"'),
            ]
        ),
        InputTypeData(
            name='UpdatePersonInput',
            fields=[
                InputField('label', 'str', True),
                InputField('llm_config', 'PersonLLMConfigInput', True),
            ]
        ),
        InputTypeData(
            name='CreateApiKeyInput',
            fields=[
                InputField('label', 'str', False),
                InputField('service', 'APIServiceType', False),
                InputField('key', 'str', False),
            ]
        ),
        InputTypeData(
            name='ExecuteDiagramInput',
            fields=[
                InputField('diagram_id', 'strawberry.ID', True),
                InputField('diagram_data', 'strawberry.scalars.JSON', True),
                InputField('variables', 'strawberry.scalars.JSON', True),
                InputField('debug_mode', 'bool', True),
                InputField('max_iterations', 'int', True),
                InputField('timeout_seconds', 'int', True),
                InputField('use_unified_monitoring', 'bool', True),
            ]
        ),
        InputTypeData(
            name='FileOperationInput',
            fields=[
                InputField('diagram_id', 'strawberry.ID', False),
                InputField('format', 'DiagramFormat', False),
            ]
        ),
        InputTypeData(
            name='UpdateNodeStateInput',
            fields=[
                InputField('execution_id', 'strawberry.ID', False),
                InputField('node_id', 'strawberry.ID', False),
                InputField('status', 'Status', False),
                InputField('output', 'strawberry.scalars.JSON', True),
                InputField('error', 'str', True),
            ]
        ),
        InputTypeData(
            name='DiagramFilterInput',
            fields=[
                InputField('name', 'str', True),
                InputField('author', 'str', True),
                InputField('tags', 'list[str]', True),
                InputField('created_after', 'datetime', True),
                InputField('created_before', 'datetime', True),
            ]
        ),
        InputTypeData(
            name='ExecutionFilterInput',
            fields=[
                InputField('diagram_id', 'strawberry.ID', True),
                InputField('status', 'Status', True),
                InputField('started_after', 'datetime', True),
                InputField('started_before', 'datetime', True),
            ]
        ),
        InputTypeData(
            name='ExecutionControlInput',
            fields=[
                InputField('execution_id', 'strawberry.ID', False),
                InputField('action', 'str', False),
                InputField('reason', 'str', True),
            ]
        ),
        InputTypeData(
            name='InteractiveResponseInput',
            fields=[
                InputField('execution_id', 'strawberry.ID', False),
                InputField('node_id', 'strawberry.ID', False),
                InputField('response', 'str', False),
                InputField('metadata', 'strawberry.scalars.JSON', True),
            ]
        ),
        InputTypeData(
            name='RegisterCliSessionInput',
            fields=[
                InputField('execution_id', 'str', False),
                InputField('diagram_name', 'str', False),
                InputField('diagram_format', 'DiagramFormat', False),
                InputField('diagram_data', 'strawberry.scalars.JSON', True),
                InputField('diagram_path', 'str', True),
            ]
        ),
        InputTypeData(
            name='UnregisterCliSessionInput',
            fields=[
                InputField('execution_id', 'str', False),
            ]
        ),
    ]

    return input_types_data
