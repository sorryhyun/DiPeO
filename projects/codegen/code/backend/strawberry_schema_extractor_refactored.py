"""
Refactored Strawberry GraphQL schema generation from operations.
Uses operations metadata instead of hard-coded return type mappings.

This is the enhanced version for the IR-based pipeline.
"""

import importlib
import inspect
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Union, get_type_hints, get_origin, get_args


def main(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Extract operations from generated operations.py file for schema generation.
    Uses operations_meta.json for return type mappings instead of hard-coded logic.

    Args:
        inputs: Can be empty dict, we'll read the operations.py directly

    Returns:
        Dictionary with 'queries' and 'mutations' lists for template
    """
    # Import the operations module
    from dipeo.diagram_generated.graphql_backups import operations

    # Load operations metadata
    meta_path = Path("/home/soryhyun/DiPeO/dipeo/diagram_generated_staged/graphql/operations_meta.json")

    ops_meta = []
    if meta_path.exists():
        ops_meta = json.loads(meta_path.read_text())
        print(f"Loaded operations metadata from {meta_path}")
        print(f"  Found {len(ops_meta)} operations in metadata")

    # Create return type lookup from metadata
    RETURNS = {m["name"]: m["returns"] for m in ops_meta}

    queries = []
    mutations = []
    subscriptions = []

    def camel_to_snake(name: str) -> str:
        """Convert CamelCase to snake_case."""
        # Insert underscore before uppercase letters that follow lowercase letters
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Insert underscore before uppercase letters that follow numbers or lowercase
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def get_return_type(operation_name: str, operation_type: str) -> str:
        """
        Map operation names to their correct return types using metadata.
        Falls back to minimal hard-coded logic only for operations not in metadata.
        """
        # First preference: metadata lookup
        if operation_name in RETURNS:
            return RETURNS[operation_name]

        # Minimal fallbacks for operations that might not be in metadata yet
        print(f"Warning: No metadata found for operation '{operation_name}', using fallback")

        if operation_type == "subscription" and operation_name == "ExecutionUpdates":
            return "ExecutionUpdate"

        # Default to JSON for unknown operations
        return "JSON"

    def extract_parameters(operation_class):
        """Extract parameters from the Variables TypedDict of an operation class."""
        parameters = []

        # Get the Variables inner class
        if hasattr(operation_class, 'Variables'):
            variables_class = operation_class.Variables

            # Try to get type hints from the TypedDict
            try:
                type_hints = get_type_hints(variables_class)

                for param_name, param_type in type_hints.items():
                    # Map Python types to GraphQL/Strawberry types
                    type_str = str(param_type)
                    optional = False

                    # Check if it's Optional (Union with None)
                    origin = get_origin(param_type)
                    if origin is Union:
                        args = get_args(param_type)
                        if type(None) in args:
                            optional = True
                            # Get the non-None type
                            param_type = next(arg for arg in args if arg != type(None))
                            type_str = str(param_type)

                    # Map the type
                    if 'dict' in type_str:
                        strawberry_type = 'JSON'
                    elif 'list' in type_str:
                        # Extract inner type
                        inner_match = re.search(r'list\[([^\]]+)\]', type_str)
                        if inner_match:
                            inner_type = inner_match.group(1)
                            # Handle dict[str, Any] -> JSON
                            if 'dict' in inner_type:
                                strawberry_type = 'list[JSON]'
                            else:
                                strawberry_type = f'list[{inner_type}]'
                        else:
                            strawberry_type = 'list[JSON]'
                    else:
                        # Use as-is for custom types
                        strawberry_type = type_str.replace('typing.', '')

                    parameters.append({
                        'name': param_name,
                        'type': strawberry_type,
                        'optional': optional
                    })
            except Exception as e:
                print(f"Error extracting parameters from {operation_class.__name__}: {e}")

        return parameters

    # Inspect the operations module for operation classes
    for name, obj in inspect.getmembers(operations):
        if inspect.isclass(obj) and name.endswith('Operation'):
            # Extract operation name from class name
            operation_name = name[:-9]  # Remove 'Operation' suffix

            # Determine operation type
            if hasattr(obj, '__annotations__'):
                # Check for query string constants to determine type
                module_dict = vars(operations)
                snake_name = camel_to_snake(operation_name).upper()

                operation_type = None
                if f"{snake_name}_QUERY" in module_dict:
                    operation_type = "query"
                elif f"{snake_name}_MUTATION" in module_dict:
                    operation_type = "mutation"
                elif f"{snake_name}_SUBSCRIPTION" in module_dict:
                    operation_type = "subscription"

                if operation_type:
                    # Extract parameters
                    parameters = extract_parameters(obj)

                    # Get return type from metadata
                    return_type = get_return_type(operation_name, operation_type)

                    # Create operation info
                    operation_info = {
                        'name': operation_name,
                        'function_name': camel_to_snake(operation_name),
                        'parameters': parameters,
                        'return_type': return_type,
                        'has_parameters': len(parameters) > 0
                    }

                    # Add to appropriate list
                    if operation_type == "query":
                        queries.append(operation_info)
                    elif operation_type == "mutation":
                        mutations.append(operation_info)
                    elif operation_type == "subscription":
                        subscriptions.append(operation_info)

    # Sort for consistent output
    queries.sort(key=lambda x: x['name'])
    mutations.sort(key=lambda x: x['name'])
    subscriptions.sort(key=lambda x: x['name'])

    print(f"Extracted {len(queries)} queries, {len(mutations)} mutations, {len(subscriptions)} subscriptions")

    # Print statistics about metadata usage
    total_ops = len(queries) + len(mutations) + len(subscriptions)
    metadata_hits = sum(1 for op in queries + mutations + subscriptions if op['name'] in RETURNS)
    print(f"Metadata coverage: {metadata_hits}/{total_ops} operations ({metadata_hits*100//total_ops if total_ops else 0}%)")

    return {
        'queries': queries,
        'mutations': mutations,
        'subscriptions': subscriptions,
        'has_queries': len(queries) > 0,
        'has_mutations': len(mutations) > 0,
        'has_subscriptions': len(subscriptions) > 0
    }
