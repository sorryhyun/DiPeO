"""
Strawberry GraphQL schema generation from operations.

Extracts operations from generated operations.py file and prepares data
for Strawberry schema template generation.
"""

import importlib
import inspect
import re
from datetime import datetime
from typing import Any, Union, get_type_hints, get_origin, get_args


def extract_operations_for_schema(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Extract operations from generated operations.py file for schema generation.

    Args:
        inputs: Can be empty dict, we'll read the operations.py directly

    Returns:
        Dictionary with 'queries' and 'mutations' lists for template
    """
    # Import the operations module
    from dipeo.diagram_generated.graphql import operations

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
        Map operation names to their correct return types.
        Return direct types for queries, Result wrappers for mutations.
        """
        # Direct type mapping for queries
        DIRECT_TYPE_MAP = {
            "Execution": "ExecutionStateType",
            "Diagram": "DomainDiagramType",
            "Person": "DomainPersonType",
            "ApiKey": "DomainApiKeyType",
            "Node": "DomainNodeType",
            # File and CliSession types don't exist yet, use JSON
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
                return "list[JSON]"  # FileType doesn't exist yet
            elif operation_name == "GetActiveCliSession":
                return "JSON"  # CliSessionType doesn't exist yet

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
                            param_type = next(t for t in args if t != type(None))
                            type_str = str(param_type)

                    # Map the type to Strawberry types
                    if param_name.endswith('_id') or param_name == 'id':
                        strawberry_type = 'strawberry.ID'
                    elif 'str' in type_str:
                        strawberry_type = 'str'
                    elif 'int' in type_str:
                        strawberry_type = 'int'
                    elif 'bool' in type_str:
                        strawberry_type = 'bool'
                    elif 'float' in type_str:
                        strawberry_type = 'float'
                    elif 'datetime' in type_str.lower():
                        strawberry_type = 'datetime'
                    elif 'Input' in type_str:
                        # Extract the input class name
                        # Handle both direct class references and string annotations
                        if '<class' in type_str:
                            # Direct class reference
                            strawberry_type = param_type.__name__
                        else:
                            # String annotation - extract the class name
                            import_match = re.search(r"'([^']+)'", type_str)
                            if import_match:
                                strawberry_type = import_match.group(1).split('.')[-1]
                            else:
                                # Fallback: extract from the type string
                                strawberry_type = type_str.split('.')[-1].replace("'", "")
                    elif 'DiagramFormatGraphQL' in type_str or 'DiagramFormat' in type_str:
                        strawberry_type = 'DiagramFormatGraphQL'
                    elif 'dict' in type_str.lower():
                        strawberry_type = 'JSON'
                    elif 'list' in type_str.lower():
                        strawberry_type = 'list[JSON]'  # Use JSON instead of Any
                    elif 'Any' in type_str:
                        strawberry_type = 'JSON'  # Map Any to JSON
                    else:
                        # Default to the type name as-is
                        strawberry_type = type_str.split('.')[-1].replace("'", "")

                    # Add Optional wrapper if needed
                    if optional:
                        strawberry_type = f'Optional[{strawberry_type}]'

                    parameters.append({
                        'name': param_name,
                        'type': strawberry_type,
                        'optional': optional
                    })
            except Exception as e:
                # If we can't extract type hints, fallback to basic inspection
                print(f"Warning: Could not extract type hints for {operation_class.__name__}: {e}")

        return parameters

    # Track field names to detect duplicates
    seen_field_names = {'query': set(), 'mutation': set(), 'subscription': set()}

    # Iterate through all members of the operations module
    for name in dir(operations):
        # Skip private and special attributes
        if name.startswith('_'):
            continue

        # Look for operation classes
        if name.endswith('Operation'):
            obj = getattr(operations, name)

            # Check if it's a class with operation_type attribute
            if inspect.isclass(obj) and hasattr(obj, 'operation_type'):
                operation_type = obj.operation_type
                operation_name = obj.operation_name  # Use the actual operation_name attribute

                # Convert to snake_case for field name
                field_name = camel_to_snake(operation_name)

                # Check for duplicates and make unique if necessary
                if field_name in seen_field_names[operation_type]:
                    # For duplicates, use the full operation name
                    print(f"Warning: Duplicate field name '{field_name}' detected for {operation_type}")
                    print(f"  Operations: {operation_name} (current)")
                    # Keep the original field name - the issue might be in the operation names themselves

                seen_field_names[operation_type].add(field_name)

                # Extract parameters from Variables TypedDict
                parameters = extract_parameters(obj)

                # Get the return type for this operation
                return_type = get_return_type(operation_name, operation_type)

                # Generate field alias for queries (noun forms)
                alias_name = None
                if operation_type == "query":
                    if field_name.startswith("get_"):
                        alias_name = field_name[4:]  # get_execution → execution
                    elif field_name.startswith("list_"):
                        alias_name = field_name[5:]  # list_executions → executions

                # Generate description
                description = f"Execute {operation_name} {operation_type}"

                operation_info = {
                    'operation_class': name,
                    'field_name': field_name,
                    'alias_name': alias_name,  # NEW: preferred noun form
                    'description': description,
                    'operation_name': operation_name,
                    'parameters': parameters,  # Add extracted parameters
                    'return_type': return_type,  # Add return type
                }

                if operation_type == 'query':
                    queries.append(operation_info)
                elif operation_type == 'mutation':
                    mutations.append(operation_info)
                elif operation_type == 'subscription':
                    subscriptions.append(operation_info)

    # Sort for consistent output
    queries.sort(key=lambda x: x['field_name'])
    mutations.sort(key=lambda x: x['field_name'])
    subscriptions.sort(key=lambda x: x['field_name'])

    return {
        'generated_at': datetime.now().isoformat(),
        'queries': queries,
        'mutations': mutations,
        'subscriptions': subscriptions,
    }
