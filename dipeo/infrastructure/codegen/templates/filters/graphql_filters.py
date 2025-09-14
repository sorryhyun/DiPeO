"""TypeScript to GraphQL type conversion filters for code generation.

This module provides filters specifically designed for converting TypeScript
type annotations to GraphQL type definitions during schema generation.
"""

import re
from typing import Any


class TypeScriptToGraphQLFilters:
    """Collection of filters for TypeScript to GraphQL type conversion."""

    TYPE_MAP = {
        "string": "String",
        "number": "Float",
        "boolean": "Boolean",
        "any": "JSON",
        "unknown": "JSON",
        "void": "JSON",
        "null": "JSON",
        "undefined": "JSON",
        "object": "JSON",
        "bigint": "BigInt",
        "symbol": "String",
        "never": "JSON",
        "Date": "DateTime",
    }

    INTEGER_FIELDS = {
        "maxIteration",
        "sequence",
        "messageCount",
        "timeout",
        "timeoutSeconds",
        "durationSeconds",
        "maxTokens",
        "statusCode",
        "totalTokens",
        "promptTokens",
        "completionTokens",
        "input",
        "output",
        "cached",
        "total",
        "retries",
        "maxRetries",
        "port",
        "x",
        "y",
        "width",
        "height",
        "count",
        "index",
        "limit",
        "offset",
        "page",
        "pageSize",
        "size",
        "length",
        "version",
    }

    BRANDED_IDS = {
        "NodeID",
        "ArrowID",
        "HandleID",
        "PersonID",
        "ApiKeyID",
        "DiagramID",
        "ExecutionID",
        "HookID",
        "TaskID",
        "MessageID",
        "ConversationID",
        "AgentID",
        "ToolID",
        "FileID",
    }

    _type_cache: dict[str, str] = {}

    @classmethod
    def ts_to_graphql_type(
        cls, ts_type: str, field_name: str = "", context: dict | None = None
    ) -> str:
        """Convert TypeScript type to GraphQL type.

        Args:
            ts_type: TypeScript type string
            field_name: Optional field name for context-specific conversions
            context: Optional context dict with additional info

        Returns:
            GraphQL type string
        """
        if not ts_type:
            return "JSON"

        cache_key = f"{ts_type}:{field_name}"
        if cache_key in cls._type_cache:
            return cls._type_cache[cache_key]

        ts_type = cls.strip_inline_comments(ts_type).strip()

        if ts_type in cls.BRANDED_IDS:
            cls._type_cache[cache_key] = "ID"
            return "ID"

        if ts_type.startswith("{") and ts_type.endswith("}"):
            result = "JSON"
            cls._type_cache[cache_key] = result
            return result

        if " | " in ts_type:
            result = "JSON"
            cls._type_cache[cache_key] = result
            return result

        array_match = re.match(r"^(.+)\[\]$", ts_type)
        if array_match:
            inner_type = cls.ts_to_graphql_type(array_match.group(1), field_name, context)
            result = f"[{inner_type}]"
            cls._type_cache[cache_key] = result
            return result

        generic_array_match = re.match(r"^Array<(.+)>$", ts_type)
        if generic_array_match:
            inner_type = cls.ts_to_graphql_type(generic_array_match.group(1), field_name, context)
            result = f"[{inner_type}]"
            cls._type_cache[cache_key] = result
            return result

        record_match = re.match(r"^Record<(.+),\s*(.+)>$", ts_type)
        if record_match:
            result = "JSON"
            cls._type_cache[cache_key] = result
            return result

        base_type = cls.TYPE_MAP.get(ts_type, ts_type)

        if base_type == "Float" and field_name in cls.INTEGER_FIELDS:
            base_type = "Int"

        cls._type_cache[cache_key] = base_type
        return base_type

    @classmethod
    def strip_inline_comments(cls, text: str) -> str:
        return re.sub(r"//.*$", "", text, flags=re.MULTILINE).strip()

    @classmethod
    def graphql_field_type(cls, field: dict[str, Any]) -> str:
        """Generate GraphQL field type from TypeScript field definition.

        Args:
            field: Field definition dict with 'type' and optionally 'required'

        Returns:
            GraphQL field type string with nullability
        """
        ts_type = field.get("type", "JSON")
        field_name = field.get("name", "")
        required = field.get("required", False)

        graphql_type = cls.ts_to_graphql_type(ts_type, field_name)

        if (required and not graphql_type.startswith("[")) or (
            required and graphql_type.startswith("[")
        ):
            graphql_type = f"{graphql_type}!"

        return graphql_type

    @classmethod
    def graphql_input_type_name(cls, type_name: str) -> str:
        if type_name.endswith("Type"):
            return type_name.replace("Type", "Input")
        return f"{type_name}Input"

    @classmethod
    def graphql_enum_value(cls, value: str) -> str:
        return re.sub(r"[^A-Z0-9_]", "_", value.upper())

    @classmethod
    def graphql_to_python_type(cls, graphql_type: str, required: bool = False) -> str:
        """Map GraphQL types to Python type hints.

        Args:
            graphql_type: GraphQL type string (e.g., 'ID', 'String', 'Int')
            required: Whether the field is required

        Returns:
            Python type hint string
        """
        # Handle array types
        if graphql_type.startswith("[") and graphql_type.endswith("]"):
            inner_type = graphql_type[1:-1].replace("!", "")
            python_type = cls.graphql_to_python_type(inner_type, True)
            return f"list[{python_type}]"

        # Remove required markers for base type mapping
        base_type = graphql_type.replace("!", "")

        # Map base types
        type_map = {
            "ID": "str",
            "String": "str",
            "Int": "int",
            "Float": "float",
            "Boolean": "bool",
            "JSON": "dict[str, Any]",
            "Upload": "Upload",  # Keep Upload type as-is for strawberry.file_uploads.Upload
            "DateTime": "str",  # DateTime as ISO 8601 string
        }

        # Check if it's a known scalar or use as-is for custom types
        python_type = type_map.get(base_type, base_type)

        # Add Optional wrapper if not required and not already marked as required
        if not required and not graphql_type.endswith("!"):
            python_type = f"Optional[{python_type}]"

        return python_type

    @classmethod
    def get_operation_return_type(cls, operation_name: str, operation_type: str) -> str:
        """Determine the return type for a GraphQL operation.

        Args:
            operation_name: Name of the operation (e.g., 'GetExecution')
            operation_type: Type of operation ('query', 'mutation', 'subscription')

        Returns:
            Python return type string
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
                return "CliSessionTypeType"

        # For subscriptions, return proper typed objects
        if operation_type == "subscription":
            if operation_name == "ExecutionUpdates":
                return "ExecutionUpdate"
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
        """Get all filters provided by this class."""
        return {
            "ts_to_graphql_type": cls.ts_to_graphql_type,
            "graphql_field_type": cls.graphql_field_type,
            "graphql_input_type_name": cls.graphql_input_type_name,
            "graphql_enum_value": cls.graphql_enum_value,
            "strip_inline_comments": cls.strip_inline_comments,
            "graphql_to_python_type": cls.graphql_to_python_type,
            "get_operation_return_type": cls.get_operation_return_type,
            "to_strawberry_type": cls.to_strawberry_type,
        }
