"""GraphQL operations extraction and processing module."""

from __future__ import annotations

from typing import Any

from dipeo.infrastructure.codegen.ir_builders.core import (
    BuildContext,
    BuildStep,
    StepResult,
    StepType,
)
from dipeo.infrastructure.codegen.ir_builders.core.base_steps import (
    BaseExtractionStep,
    BaseTransformStep,
)
from dipeo.infrastructure.codegen.ir_builders.type_system_unified import UnifiedTypeConverter


class ExtractGraphQLOperationsStep(BaseExtractionStep):
    """Step to extract GraphQL operations from TypeScript AST.

    Migrated to use BaseExtractionStep template method pattern for reduced code duplication.
    """

    def __init__(self):
        """Initialize GraphQL operations extraction step."""
        super().__init__(name="extract_graphql_operations", required=True)

    def should_process_file(self, file_path: str, file_data: dict[str, Any]) -> bool:
        """Filter to only process query definition files.

        Args:
            file_path: Path to the AST file
            file_data: AST data for the file

        Returns:
            True if file contains query definitions
        """
        return "query-definitions" in file_path or "queryDefinitions" in file_path

    def extract_from_file(
        self,
        file_path: str,
        file_data: dict[str, Any],
        type_converter: UnifiedTypeConverter,
        context: BuildContext,
    ) -> list[dict[str, Any]]:
        """Extract GraphQL operations from a single AST file.

        Args:
            file_path: Path to the AST file
            file_data: AST data for the file
            type_converter: Type converter instance
            context: Build context

        Returns:
            List of extracted operation definitions
        """
        operations = []

        # Extract from constants
        constants = file_data.get("constants", [])
        for const in constants:
            const_name = const.get("name", "")
            if const_name.endswith("Queries") or const_name.endswith("Operations"):
                self._process_query_constant(const, operations, type_converter)

        return operations

    def get_metadata(self, extracted_data: list[Any]) -> dict[str, Any]:
        """Generate metadata for extraction result.

        Args:
            extracted_data: Extracted operations

        Returns:
            Metadata with operation counts by type
        """
        # Group operations by type for metadata
        operation_types = {}
        for op in extracted_data:
            op_type = op.get("type", "query")
            operation_types[op_type] = operation_types.get(op_type, 0) + 1

        return {
            "total_operations": len(extracted_data),
            "operation_types": operation_types,
        }

    def _process_query_constant(
        self,
        const: dict[str, Any],
        operations: list[dict[str, Any]],
        type_converter: UnifiedTypeConverter,
    ) -> None:
        """Process a query constant and extract operations.

        Args:
            const: Constant definition from AST
            operations: List to append operations to
            type_converter: Type converter instance
        """
        const_value = const.get("value", {})
        if not isinstance(const_value, dict):
            return

        entity_name = const_value.get("entity", "Unknown")
        queries = const_value.get("queries", [])

        for query in queries:
            if not isinstance(query, dict):
                continue

            operation = self._build_operation(query, entity_name, type_converter)
            operations.append(operation)

    def _build_operation(
        self, query: dict[str, Any], entity_name: str, type_converter: UnifiedTypeConverter
    ) -> dict[str, Any]:
        """Build an operation definition from query data.

        Args:
            query: Query definition
            entity_name: Entity name for the query
            type_converter: Type converter instance

        Returns:
            Operation definition dictionary
        """
        # Extract operation type
        raw_type = query.get("type", "query")
        operation_type = self._extract_operation_type(raw_type)

        # Process variables
        variables = self._transform_variables(query.get("variables", []), type_converter)

        # Process fields
        fields = self._transform_fields(query.get("fields", []))

        operation_name = query.get("name", "UnknownOperation")

        return {
            "name": operation_name,
            "operation_name": operation_name,
            "type": operation_type,
            "entity": entity_name,
            "variables": variables,
            "fields": fields,
            "description": query.get("description", ""),
            "return_type": query.get("returnType"),
        }

    def _extract_operation_type(self, type_value: Any) -> str:
        """Extract operation type from query definition.

        Args:
            type_value: Raw type value from AST

        Returns:
            Operation type string (query, mutation, subscription)
        """
        if isinstance(type_value, str):
            if "." in type_value:
                return type_value.split(".")[-1].lower()
            return type_value.lower()
        return "query"

    def _transform_variables(
        self, variables: list[dict[str, Any]], type_converter: UnifiedTypeConverter
    ) -> list[dict[str, Any]]:
        """Transform GraphQL variables.

        Args:
            variables: Raw variable definitions
            type_converter: Type converter instance

        Returns:
            Transformed variable definitions
        """
        transformed = []
        for var in variables:
            var_type = var.get("type", "String")
            transformed.append(
                {
                    "name": var.get("name", ""),
                    "type": var_type,
                    "graphql_type": var_type,
                    "python_type": type_converter.graphql_to_python(var_type),
                    "typescript_type": type_converter.graphql_to_ts(var_type),
                    "required": var.get("required", False),
                    "description": var.get("description", ""),
                    "default": var.get("default"),
                }
            )
        return transformed

    def _transform_fields(self, fields: Any) -> list[dict[str, Any]]:
        """Transform GraphQL fields.

        Args:
            fields: Raw field definitions

        Returns:
            Transformed field definitions
        """
        if not fields:
            return []

        if isinstance(fields, str):
            # Parse string representation of fields
            field_names = fields.strip().split()
            return [{"name": name, "fields": []} for name in field_names]

        if isinstance(fields, list):
            transformed = []
            for field in fields:
                if isinstance(field, str):
                    transformed.append({"name": field, "fields": []})
                elif isinstance(field, dict):
                    field_def = {
                        "name": field.get("name", ""),
                        "fields": self._transform_fields(field.get("fields", [])),
                        "type": field.get("type"),
                        "description": field.get("description", ""),
                    }
                    # Preserve args if present (for mutations/queries with arguments)
                    if "args" in field:
                        field_def["args"] = field.get("args", [])
                    transformed.append(field_def)
            return transformed

        return []


class BuildOperationStringsStep(BaseTransformStep):
    """Step to build GraphQL operation strings from definitions.

    Migrated to use BaseTransformStep template method pattern for reduced code duplication.
    """

    def __init__(self):
        """Initialize operation string builder step."""
        super().__init__(name="build_operation_strings", required=False)

    def get_dependency_names(self) -> list[str]:
        """Get required dependencies.

        Returns:
            List with extract_graphql_operations dependency
        """
        return ["extract_graphql_operations"]

    def extract_input_from_dependencies(
        self, input_data: Any, context: BuildContext
    ) -> list[dict[str, Any]]:
        """Extract operations list from dependency data.

        Args:
            input_data: Input data from pipeline
            context: Build context

        Returns:
            List of operations
        """
        # Handle input from dependencies
        if isinstance(input_data, dict) and "extract_graphql_operations" in input_data:
            return input_data["extract_graphql_operations"]
        elif isinstance(input_data, list):
            return input_data
        else:
            return []

    def transform_data(self, input_data: Any, context: BuildContext) -> dict[str, str]:
        """Transform operations into GraphQL operation strings.

        Args:
            input_data: List of operations
            context: Build context

        Returns:
            Dictionary mapping operation names to GraphQL strings
        """
        return self._build_operation_strings(input_data)

    def get_transform_metadata(
        self, input_data: Any, transformed_data: Any
    ) -> dict[str, Any]:
        """Generate metadata for transformation result.

        Args:
            input_data: Input operations
            transformed_data: Generated operation strings

        Returns:
            Metadata with operation count
        """
        return {
            "operation_count": len(transformed_data),
            "transform": self.name,
        }

    def _build_operation_strings(self, operations: list[dict[str, Any]]) -> dict[str, str]:
        """Build GraphQL operation strings.

        Args:
            operations: List of operation definitions

        Returns:
            Dictionary mapping operation names to GraphQL strings
        """
        operation_strings = {}

        for op in operations:
            op_name = op.get("name", "")
            if not op_name:
                continue

            op_type = op.get("type", "query")
            variables = op.get("variables", [])
            fields = op.get("fields", [])

            # Build variable declarations
            var_decls = self._build_variable_declarations(variables)

            # Construct operation string
            op_string = f"{op_type} {op_name}"
            if var_decls:
                op_string += f"({var_decls})"
            op_string += " {\n"

            # Handle fields - check if first field is a mutation/query call with explicit name
            if fields and len(fields) == 1 and "args" in fields[0]:
                # This is a mutation/query call - use it directly
                field = fields[0]
                field_name = field.get("name", "")
                args = field.get("args", [])
                sub_fields = field.get("fields", [])

                # Build the field call (convert to camelCase for GraphQL)
                op_string += f"  {self._to_camel_case(field_name)}"

                # Add args if present
                if args:
                    arg_strs = []
                    for arg in args:
                        arg_name = arg.get("name", "")
                        arg_value = arg.get("value", "")
                        is_var = arg.get("isVariable", False)
                        # Keep argument name in original format (snake_case)
                        if is_var:
                            arg_strs.append(f"{arg_name}: ${arg_value}")
                        else:
                            arg_strs.append(f"{arg_name}: {arg_value}")
                    op_string += f"({', '.join(arg_strs)})"

                op_string += " {\n"
                # Build sub-fields (return type fields)
                field_selections = self._build_field_selections(sub_fields, indent=2)
                op_string += field_selections
                op_string += "  }\n"
            else:
                # Legacy/simple case - just build field selections
                field_selections = self._build_field_selections(fields, indent=1)
                op_string += field_selections

            op_string += "}"

            operation_strings[op_name] = op_string

        return operation_strings

    def _build_variable_declarations(self, variables: list[dict[str, Any]]) -> str:
        """Build GraphQL variable declarations.

        Args:
            variables: Variable definitions

        Returns:
            Variable declaration string
        """
        if not variables:
            return ""

        var_decls = []
        for var in variables:
            var_name = var.get("name", "")
            var_type = var.get("graphql_type", "String")
            required = var.get("required", False)
            if required:
                var_type += "!"
            var_decls.append(f"${var_name}: {var_type}")

        return ", ".join(var_decls)

    def _build_field_selections(self, fields: list[dict[str, Any]], indent: int = 2) -> str:
        """Build GraphQL field selections.

        Args:
            fields: Field definitions
            indent: Indentation level

        Returns:
            Field selection string
        """
        if not fields:
            return "    id\n"  # Default field

        lines = []
        indent_str = "  " * indent
        for field in fields:
            field_name = field.get("name", "")
            sub_fields = field.get("fields", [])

            # Keep field name in original format (snake_case)
            # No conversion needed as fields are defined in snake_case in the schema

            if sub_fields:
                lines.append(f"{indent_str}{field_name} {{")
                lines.append(self._build_field_selections(sub_fields, indent + 1))
                lines.append(f"{indent_str}}}")
            else:
                lines.append(f"{indent_str}{field_name}")

        return "\n".join(lines) + "\n"

    def _to_camel_case(self, name: str) -> str:
        """Convert name to camel case.

        Args:
            name: Name to convert

        Returns:
            Camel case version
        """
        if not name:
            return ""

        # Handle snake_case (e.g., execute_diagram → executeDiagram)
        if '_' in name:
            parts = name.split('_')
            return parts[0] + ''.join(word.capitalize() for word in parts[1:])

        # Handle already camel case
        if name[0].islower():
            return name

        # Convert from PascalCase (e.g., ExecuteDiagram → executeDiagram)
        return name[0].lower() + name[1:]


class GroupOperationsByEntityStep(BaseTransformStep):
    """Step to group operations by entity for organization.

    Migrated to use BaseTransformStep template method pattern for reduced code duplication.
    """

    def __init__(self):
        """Initialize operation grouping step."""
        super().__init__(name="group_operations_by_entity", required=False)

    def get_dependency_names(self) -> list[str]:
        """Get required dependencies.

        Returns:
            List with extract_graphql_operations dependency
        """
        return ["extract_graphql_operations"]

    def extract_input_from_dependencies(
        self, input_data: Any, context: BuildContext
    ) -> list[dict[str, Any]]:
        """Extract operations list from dependency data.

        Args:
            input_data: Input data from pipeline
            context: Build context

        Returns:
            List of operations
        """
        # Handle input from dependencies
        if isinstance(input_data, dict) and "extract_graphql_operations" in input_data:
            return input_data["extract_graphql_operations"]
        elif isinstance(input_data, list):
            return input_data
        else:
            return []

    def transform_data(
        self, input_data: Any, context: BuildContext
    ) -> dict[str, list[dict[str, Any]]]:
        """Transform operations into entity-grouped structure.

        Args:
            input_data: List of operations
            context: Build context

        Returns:
            Dictionary mapping entity names to operations
        """
        return self._group_by_entity(input_data)

    def get_transform_metadata(
        self, input_data: Any, transformed_data: Any
    ) -> dict[str, Any]:
        """Generate metadata for transformation result.

        Args:
            input_data: Input operations
            transformed_data: Grouped operations

        Returns:
            Metadata with entity and operation counts
        """
        return {
            "entity_count": len(transformed_data),
            "total_operations": sum(len(ops) for ops in transformed_data.values()),
            "transform": self.name,
        }

    def _group_by_entity(self, operations: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
        """Group operations by entity.

        Args:
            operations: List of operation definitions

        Returns:
            Dictionary mapping entity names to operations
        """
        grouped = {}
        for op in operations:
            entity = op.get("entity", "Unknown")
            if entity not in grouped:
                grouped[entity] = []
            grouped[entity].append(op)
        return grouped
