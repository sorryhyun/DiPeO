"""GraphQL operations extraction and processing module."""

from __future__ import annotations

from typing import Any

from dipeo.infrastructure.codegen.ir_builders.core import (
    BuildContext,
    BuildStep,
    StepResult,
    StepType,
)
from dipeo.infrastructure.codegen.ir_builders.utils import TypeConverter


class ExtractGraphQLOperationsStep(BuildStep):
    """Step to extract GraphQL operations from TypeScript AST."""

    def __init__(self):
        """Initialize GraphQL operations extraction step."""
        super().__init__(
            name="extract_graphql_operations", step_type=StepType.EXTRACT, required=True
        )

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Extract GraphQL operations from AST data.

        Args:
            context: Build context with utilities
            input_data: TypeScript AST data

        Returns:
            StepResult with extracted operations
        """
        if not isinstance(input_data, dict):
            return StepResult(success=False, error="Input data must be a dictionary of AST files")

        type_converter = context.type_converter
        operations = self._extract_operations(input_data, type_converter)

        # Group operations by type for metadata
        operation_types = {}
        for op in operations:
            op_type = op.get("type", "query")
            operation_types[op_type] = operation_types.get(op_type, 0) + 1

        return StepResult(
            success=True,
            data=operations,
            metadata={
                "total_operations": len(operations),
                "operation_types": operation_types,
            },
        )

    def _extract_operations(
        self, ast_data: dict[str, Any], type_converter: TypeConverter
    ) -> list[dict[str, Any]]:
        """Extract all GraphQL operations from AST.

        Args:
            ast_data: TypeScript AST data
            type_converter: Type converter instance

        Returns:
            List of operation definitions
        """
        operations = []

        for file_path, file_data in ast_data.items():
            # Focus on query definition files
            if "query-definitions" not in file_path and "queryDefinitions" not in file_path:
                continue

            # Extract from constants
            constants = file_data.get("constants", [])
            for const in constants:
                const_name = const.get("name", "")
                if const_name.endswith("Queries") or const_name.endswith("Operations"):
                    self._process_query_constant(const, operations, type_converter)

        return operations

    def _process_query_constant(
        self,
        const: dict[str, Any],
        operations: list[dict[str, Any]],
        type_converter: TypeConverter,
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
        self, query: dict[str, Any], entity_name: str, type_converter: TypeConverter
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
        self, variables: list[dict[str, Any]], type_converter: TypeConverter
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


class BuildOperationStringsStep(BuildStep):
    """Step to build GraphQL operation strings from definitions."""

    def __init__(self):
        """Initialize operation string builder step."""
        super().__init__(
            name="build_operation_strings", step_type=StepType.TRANSFORM, required=False
        )
        self.add_dependency("extract_graphql_operations")

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Build GraphQL operation strings.

        Args:
            context: Build context
            input_data: Dictionary with operations from extraction step

        Returns:
            StepResult with operation strings
        """
        # Handle input from dependencies
        if isinstance(input_data, dict) and "extract_graphql_operations" in input_data:
            operations = input_data["extract_graphql_operations"]
        elif isinstance(input_data, list):
            operations = input_data
        else:
            return StepResult(success=False, error="Expected operations as input")

        operation_strings = self._build_operation_strings(operations)

        return StepResult(
            success=True,
            data=operation_strings,
            metadata={
                "operation_count": len(operation_strings),
            },
        )

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


class GroupOperationsByEntityStep(BuildStep):
    """Step to group operations by entity for organization."""

    def __init__(self):
        """Initialize operation grouping step."""
        super().__init__(
            name="group_operations_by_entity", step_type=StepType.TRANSFORM, required=False
        )
        self.add_dependency("extract_graphql_operations")

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Group operations by entity.

        Args:
            context: Build context
            input_data: Dictionary with operations from extraction step

        Returns:
            StepResult with grouped operations
        """
        # Handle input from dependencies
        if isinstance(input_data, dict) and "extract_graphql_operations" in input_data:
            operations = input_data["extract_graphql_operations"]
        elif isinstance(input_data, list):
            operations = input_data
        else:
            return StepResult(success=False, error="Expected operations as input")

        grouped = self._group_by_entity(operations)

        return StepResult(
            success=True,
            data=grouped,
            metadata={
                "entity_count": len(grouped),
                "total_operations": sum(len(ops) for ops in grouped.values()),
            },
        )

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
