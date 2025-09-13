"""
Enhanced version of prepare_python_graphql_data.py that also generates operations metadata.
This module adds metadata generation for the IR-based strawberry pipeline.
"""

import json
import os
import sys
from pathlib import Path
from typing import Any, Optional

sys.path.append(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))

# Import the original functions
from projects.codegen.code.backend.prepare_python_graphql_data import (
    map_graphql_type_to_python,
    extract_query_string,
    build_field_string,
    to_snake_case,
    to_pascal_case,
    transform_query_to_operation,
    collect_required_imports
)


def get_return_type_for_operation(operation_name: str, operation_type: str) -> str:
    """
    Determine the return type for an operation.
    This replaces the hard-coded logic in strawberry_schema_extractor.py.
    """
    # Direct type mapping for queries
    DIRECT_TYPE_MAP = {
        "Execution": "ExecutionStateType",
        "Diagram": "DomainDiagramType",
        "Person": "DomainPersonType",
        "ApiKey": "DomainApiKeyType",
        "Node": "DomainNodeType",
        "File": "FileTypeType",
        "CliSession": "CliSessionType",
    }

    if operation_type == "query":
        # Extract entity from operation name for direct type returns
        if operation_name.startswith("Get"):
            entity = operation_name[3:]  # GetExecution → Execution
            return DIRECT_TYPE_MAP.get(entity, "JSON")
        elif operation_name.startswith("List"):
            # ListExecutions → list[ExecutionStateType]
            entity_plural = operation_name[4:]  # ListExecutions → Executions
            # Remove trailing 's' to get singular
            entity = entity_plural.rstrip('s')
            base_type = DIRECT_TYPE_MAP.get(entity, "JSON")
            return f"list[{base_type}]"
        elif operation_name == "GetExecutions":
            # Special case for GetExecutions (returns list)
            return "list[ExecutionStateType]"
        elif operation_name == "SearchDiagrams":
            return "list[DomainDiagramType]"
        elif operation_name == "GetRecentFiles":
            return "list[FileTypeType]"
        elif operation_name == "GetActiveCliSession":
            return "CliSessionTypeType"

    # For subscriptions, return proper typed objects
    if operation_type == "subscription":
        if operation_name == "ExecutionUpdates":
            return "ExecutionUpdate"
        # Other subscriptions can return JSON for now
        return "JSON"

    # For mutations, keep existing Result wrappers
    # Execution operations
    if operation_name in ['ExecuteDiagram', 'UpdateNodeState', 'ControlExecution', 'SendInteractiveResponse']:
        return 'ExecutionResult'

    # Diagram operations
    if operation_name in ['CreateDiagram', 'UpdateDiagram', 'LoadDiagram', 'SaveDiagram']:
        return 'DiagramResult'
    if operation_name == 'DeleteDiagram':
        return 'DeleteResult'

    # Node operations
    if operation_name in ['CreateNode', 'UpdateNode']:
        return 'NodeResult'
    if operation_name == 'DeleteNode':
        return 'DeleteResult'

    # Person operations
    if operation_name in ['CreatePerson', 'UpdatePerson']:
        return 'PersonResult'
    if operation_name == 'DeletePerson':
        return 'DeleteResult'

    # API Key operations
    if operation_name in ['CreateApiKey', 'TestApiKey']:
        return 'ApiKeyResult'
    if operation_name == 'DeleteApiKey':
        return 'DeleteResult'

    # Format conversion
    if operation_name == 'ConvertDiagramFormat':
        return 'FormatConversionResult'

    # CLI session operations
    if operation_name in ['RegisterCliSession', 'UnregisterCliSession']:
        return 'CliSessionResult'

    # File operations (mutations)
    if operation_name in ['SaveFile', 'DeleteFile']:
        return 'FileOperationResult'

    # Default to JSON for unknown operations
    return 'JSON'


def generate_operations_metadata(operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Generate operations metadata for the IR-based pipeline.

    Args:
        operations: List of operation dictionaries

    Returns:
        List of metadata dictionaries for each operation
    """
    metadata = []

    for op in operations:
        meta = {
            "name": op['name'],
            "kind": op['type'],  # query, mutation, subscription
            "returns": get_return_type_for_operation(op['name'], op['type']),
            "variables": []
        }

        # Add variable metadata
        for var in op.get('variables', []):
            var_meta = {
                "name": var['name'],
                "type": var['graphql_type'],
                "required": var['required']
            }
            meta["variables"].append(var_meta)

        # Add description if available
        if 'description' in op:
            meta["description"] = op['description']

        metadata.append(meta)

    return metadata


def main(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Enhanced version that also generates operations metadata.

    Args:
        inputs: Contains 'ast_data' with parsed TypeScript AST

    Returns:
        Structured data for template generation with metadata
    """
    ast_data = inputs.get('ast_data', {})
    operations = []

    # Process each query definition file
    for key, file_data in ast_data.items():
        if not key or not file_data:
            continue

        # Skip non-query-definition files
        if 'query-definitions' not in key or key.endswith('types.ts.json'):
            continue

        # Extract queries from constants
        if 'constants' in file_data:
            for const in file_data['constants']:
                const_value = const.get('value', {})
                if isinstance(const_value, dict) and 'queries' in const_value:
                    entity = const_value.get('entity', 'Unknown')

                    for query in const_value.get('queries', []):
                        operation = transform_query_to_operation(query, entity)
                        if operation:
                            operations.append(operation)

    # Sort operations by type and name for consistent output
    operations.sort(key=lambda x: (x['type'], x['name']))

    # Group by type
    queries = [op for op in operations if op['type'] == 'query']
    mutations = [op for op in operations if op['type'] == 'mutation']
    subscriptions = [op for op in operations if op['type'] == 'subscription']

    # Collect all required imports
    imports = collect_required_imports(operations)

    # Generate metadata
    metadata = generate_operations_metadata(operations)

    # Save metadata to file
    metadata_path = Path('/home/soryhyun/DiPeO/dipeo/diagram_generated_staged/graphql/operations_meta.json')
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.write_text(json.dumps(metadata, indent=2))

    print(f"Generated operations metadata with {len(metadata)} operations")
    print(f"  - Queries: {len(queries)}")
    print(f"  - Mutations: {len(mutations)}")
    print(f"  - Subscriptions: {len(subscriptions)}")

    return {
        'operations': operations,
        'queries': queries,
        'mutations': mutations,
        'subscriptions': subscriptions,
        'imports': imports,
        'metadata': {
            'total_operations': len(operations),
            'total_queries': len(queries),
            'total_mutations': len(mutations),
            'total_subscriptions': len(subscriptions),
            'operations_meta': metadata  # Include metadata in response
        }
    }
