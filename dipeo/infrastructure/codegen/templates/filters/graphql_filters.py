"""GraphQL-specific transformation filters for code generation.

This module provides filters for GraphQL-specific transformations including
field types, input type names, enum values, and operation return types.
"""

import re
from typing import Any


class GraphQLFilters:
    """GraphQL-specific transformation filters."""

    @classmethod
    def graphql_field_type(cls, field: dict[str, Any]) -> str:
        """Generate GraphQL field type with nullability markers.

        Args:
            field: Field definition dict with 'type' and optionally 'required'

        Returns:
            GraphQL field type string with nullability markers
        """
        graphql_type = field.get("type", "JSON")
        required = field.get("required", False)

        if required and not graphql_type.endswith("!"):
            graphql_type = f"{graphql_type}!"

        return graphql_type

    @classmethod
    def graphql_input_type_name(cls, type_name: str) -> str:
        """Generate GraphQL input type name from a base type name.

        Args:
            type_name: Base type name (e.g., 'ExecutionType')

        Returns:
            GraphQL input type name (e.g., 'ExecutionInput')
        """
        if type_name.endswith("Type"):
            return type_name.replace("Type", "Input")
        return f"{type_name}Input"

    @classmethod
    def graphql_enum_value(cls, value: str) -> str:
        """Convert a value to a valid GraphQL enum value.

        Args:
            value: The original value

        Returns:
            GraphQL-compliant enum value (uppercase with underscores)
        """
        return re.sub(r"[^A-Z0-9_]", "_", value.upper())

    @classmethod
    def get_operation_return_type(cls, operation_name: str, operation_type: str) -> str:
        """Determine the Python return type for a GraphQL operation.

        Maps GraphQL operation names to their corresponding Python return types
        based on the operation type and naming conventions.

        Args:
            operation_name: Name of the operation (e.g., 'GetExecution')
            operation_type: Type of operation ('query', 'mutation', 'subscription')

        Returns:
            Python return type string for the operation
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

        # Queries that can return None (nullable)
        NULLABLE_QUERIES = {
            "GetExecution",  # Execution might not exist yet
        }

        if operation_type == "query":
            # Extract entity from operation name for direct type returns
            if operation_name.startswith("Get"):
                entity = operation_name[3:]  # GetExecution → Execution
                base_type = DIRECT_TYPE_MAP.get(entity, "JSON")
                # Make nullable for queries that can return None
                if operation_name in NULLABLE_QUERIES:
                    return f"Optional[{base_type}]"
                return base_type
            elif operation_name.startswith("List"):
                # ListExecutions → list[ExecutionStateType]
                entity_plural = operation_name[4:]  # ListExecutions → Executions
                # Remove trailing 's' to get singular
                entity = entity_plural.rstrip("s")
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
                return "Optional[JSON]"

        # For subscriptions, return proper typed objects
        if operation_type == "subscription":
            if operation_name == "ExecutionUpdates":
                return "ExecutionUpdateType"
            # Other subscriptions can return JSON for now
            return "JSON"

        # For mutations, keep existing Result wrappers
        # Execution operations
        if operation_name in [
            "ExecuteDiagram",
            "UpdateNodeState",
            "ControlExecution",
            "SendInteractiveResponse",
        ]:
            return "ExecutionResult"

        # Diagram operations
        if operation_name in ["CreateDiagram", "UpdateDiagram", "LoadDiagram", "SaveDiagram"]:
            return "DiagramResult"
        if operation_name == "DeleteDiagram":
            return "DeleteResult"

        # Node operations
        if operation_name in ["CreateNode", "UpdateNode"]:
            return "NodeResult"
        if operation_name == "DeleteNode":
            return "DeleteResult"

        # Person operations
        if operation_name in ["CreatePerson", "UpdatePerson"]:
            return "PersonResult"
        if operation_name == "DeletePerson":
            return "DeleteResult"

        # API Key operations
        if operation_name in ["CreateApiKey", "TestApiKey"]:
            return "ApiKeyResult"
        if operation_name == "DeleteApiKey":
            return "DeleteResult"

        # Format conversion
        if operation_name == "ConvertDiagramFormat":
            return "FormatConversionResult"

        # CLI session operations
        if operation_name in ["RegisterCliSession", "UnregisterCliSession"]:
            return "CliSessionResult"

        # File operations (mutations)
        if operation_name in ["SaveFile", "DeleteFile"]:
            return "FileOperationResult"

        # Default to JSON for unknown operations
        return "JSON"

    @classmethod
    def to_strawberry_type(cls, py_type: str) -> str:
        """Convert Python type to Strawberry GraphQL type.

        Args:
            py_type: Python type string

        Returns:
            Strawberry type string
        """
        # Map Python types to Strawberry types
        type_map = {
            "str": "str",
            "int": "int",
            "float": "float",
            "bool": "bool",
            "dict": "JSON",
            "Dict": "JSON",
            "Dict[str, Any]": "JSON",
            "dict[str, Any]": "JSON",
            "list": "List",
            "List": "List",
            "Optional": "Optional",
            "Any": "JSON",
            "datetime": "DateTime",
        }

        # Handle Optional types
        if py_type.startswith("Optional["):
            inner_type = py_type[9:-1]
            return f"Optional[{cls.to_strawberry_type(inner_type)}]"

        # Handle List types
        if py_type.startswith("List[") or py_type.startswith("list["):
            inner_type = py_type[5:-1]
            return f"List[{cls.to_strawberry_type(inner_type)}]"

        # Direct mapping or return as-is
        return type_map.get(py_type, py_type)

    @classmethod
    def get_all_filters(cls) -> dict[str, Any]:
        """Get all GraphQL-specific filters provided by this class.

        Returns:
            Dictionary mapping filter names to filter methods
        """
        return {
            "graphql_field_type": cls.graphql_field_type,
            "graphql_input_type_name": cls.graphql_input_type_name,
            "graphql_enum_value": cls.graphql_enum_value,
            "get_operation_return_type": cls.get_operation_return_type,
            "to_strawberry_type": cls.to_strawberry_type,
        }
