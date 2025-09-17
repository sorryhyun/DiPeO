"""Strawberry (GraphQL) IR builder implementation."""

from __future__ import annotations

import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from dipeo.domain.codegen.ir_builder_port import IRData
from dipeo.infrastructure.codegen.ir_builders.base import BaseIRBuilder
from dipeo.infrastructure.codegen.ir_builders.utils import (
    TypeConverter,
    extract_constants_from_ast,
    extract_interfaces_from_ast,
    load_yaml_config,
    pascal_case,
    snake_to_pascal,
)
from dipeo.infrastructure.codegen.type_resolver import StrawberryTypeResolver

logger = logging.getLogger(__name__)


# NOTE: Type conversion functions moved to shared utils and template filters
# See dipeo/infrastructure/codegen/ir_builders/utils.py
# See dipeo/infrastructure/codegen/templates/filters/graphql_filters.py


# ============================================================================
# CONFIGURATION
# ============================================================================


class StrawberryConfig:
    def __init__(self, root: Path):
        self.root = root
        self.type_mappings = self._load("type_mappings.yaml")
        self.domain_fields = self._load("domain_fields.yaml")
        self.schema = self._opt("schema_config.yaml")

    def _load(self, name: str) -> dict[str, Any]:
        with open(self.root / name) as f:
            return yaml.safe_load(f) or {}

    def _opt(self, name: str) -> dict[str, Any]:
        p = self.root / name
        return self._load(name) if p.exists() else {}

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        return {
            "type_mappings": self.type_mappings,
            "domain_fields": self.domain_fields,
            "schema": self.schema,
        }


# ============================================================================
# OPERATIONS EXTRACTION
# ============================================================================

# NOTE: get_return_type_for_operation moved to template filters
# See dipeo/infrastructure/codegen/templates/filters/graphql_filters.py


def extract_query_string(query_data: dict[str, Any]) -> str:
    """
    Reconstruct the GraphQL query string from parsed AST data.
    """
    # Extract operation type from enum value (e.g., "QueryOperationType.QUERY" -> "query")
    type_value = query_data.get("type", "query")
    if "." in type_value:
        operation_type = type_value.split(".")[-1].lower()
    else:
        operation_type = type_value.lower()

    name = query_data.get("name", "UnknownOperation")
    variables = query_data.get("variables", [])
    fields = query_data.get("fields", [])

    # Build variables string
    vars_str = ""
    if variables:
        vars_parts = []
        for var in variables:
            var_name = var.get("name", "")
            var_type = var.get("type", "String")
            required = var.get("required", False)
            if required:
                var_type = f"{var_type}!"
            vars_parts.append(f"${var_name}: {var_type}")
        vars_str = f"({', '.join(vars_parts)})"

    # Build fields string using helper
    fields_str = ""
    if fields:
        field_strings = []
        for field in fields:
            field_str = build_field_string(
                field, indent=2, operation_type=operation_type, operation_name=name
            )
            if field_str:
                field_strings.append(field_str)
        fields_str = "\n".join(field_strings)

    # Build complete query
    query = f"{operation_type} {name}{vars_str} {{\n{fields_str}\n}}"
    return query


def build_field_string(
    field: dict[str, Any],
    indent: int = 0,
    operation_type: str | None = None,
    operation_name: str | None = None,
) -> str:
    """
    Build a GraphQL field string from field data, including nested fields.
    Special handling for mutations vs queries.
    """
    if isinstance(field, str):
        return "  " * indent + field

    field_name = field.get("name", "")

    # Special transformations for queries to handle noun/verb confusion
    # This happens because TypeScript definitions sometimes use verbs for queries
    if operation_type == "query" and operation_name:
        # Check if this is a top-level field of a query
        if indent == 2:  # Top-level field
            field_name = transform_query_field_to_noun(field_name)

    # Handle field arguments
    args_str = ""
    if "args" in field:
        args_parts = []
        for arg in field["args"]:
            arg_name = arg.get("name", "")
            # Use variable reference
            args_parts.append(f"{arg_name}: ${arg_name}")
        if args_parts:
            args_str = f"({', '.join(args_parts)})"

    # Handle nested fields
    nested_str = ""
    nested_fields = field.get("fields", [])
    if nested_fields:
        nested_parts = []
        for nested in nested_fields:
            nested_str_part = build_field_string(nested, indent + 1, operation_type, operation_name)
            if nested_str_part:
                nested_parts.append(nested_str_part)
        if nested_parts:
            nested_str = " {\n" + "\n".join(nested_parts) + "\n" + "  " * indent + "}"

    return "  " * indent + field_name + args_str + nested_str


def transform_query_field_to_noun(field_name: str) -> str:
    """
    Transform query field names from verbs to nouns if needed.
    This handles common TypeScript patterns where queries are defined with verb names.
    """
    # Common verb-to-noun transformations
    verb_to_noun_map = {
        # Get operations
        "getExecution": "execution",
        "getExecutions": "executions",
        "getDiagram": "diagram",
        "getDiagrams": "diagrams",
        "getNode": "node",
        "getNodes": "nodes",
        "getConversation": "conversation",
        "getConversations": "conversations",
        "getPerson": "person",
        "getPersons": "persons",
        "getCurrentUser": "currentUser",
        "getStatus": "status",
        # List operations
        "listExecutions": "executions",
        "listDiagrams": "diagrams",
        "listNodes": "nodes",
        "listConversations": "conversations",
        "listPersons": "persons",
        # Search operations
        "searchDiagrams": "searchDiagrams",  # Keep as-is, it's already noun-ish
        "searchNodes": "searchNodes",
        # Check operations
        "checkStatus": "status",
        "checkHealth": "health",
        # Fetch operations
        "fetchExecution": "execution",
        "fetchDiagram": "diagram",
    }

    # Check if field needs transformation
    if field_name in verb_to_noun_map:
        return verb_to_noun_map[field_name]

    # Generic transformations
    if field_name.startswith("get"):
        # Remove 'get' prefix and lowercase first letter
        base = field_name[3:]
        if base:
            return base[0].lower() + base[1:]

    if field_name.startswith("list"):
        # Remove 'list' prefix and lowercase first letter
        base = field_name[4:]
        if base:
            return base[0].lower() + base[1:]

    if field_name.startswith("fetch"):
        # Remove 'fetch' prefix and lowercase first letter
        base = field_name[5:]
        if base:
            return base[0].lower() + base[1:]

    # Return as-is if no transformation needed
    return field_name


def transform_query_to_operation(
    query_data: dict[str, Any], entity: str
) -> Optional[dict[str, Any]]:
    """
    Transform a raw query definition into a proper operation structure.
    """
    if not query_data:
        return None

    # Extract operation type from enum value (e.g., "QueryOperationType.QUERY" -> "query")
    type_value = query_data.get("type", "query")
    if "." in type_value:
        operation_type = type_value.split(".")[-1].lower()
    else:
        operation_type = type_value.lower()

    # Get operation name
    name = query_data.get("name", "")
    if not name:
        return None

    # Transform variables
    variables = []
    for var in query_data.get("variables", []):
        var_type = var.get("type", "String")
        variables.append(
            {
                "name": var.get("name", ""),
                "type": var_type,
                "graphql_type": var_type,  # Keep original GraphQL type
                "python_type": var_type,  # Will be converted by template filters
                "required": var.get("required", False),
            }
        )

    # Transform fields
    fields = query_data.get("fields", [])

    # Build the operation
    operation = {
        "name": name,
        "type": operation_type,
        "entity": entity,
        "variables": variables,
        "fields": fields,
    }

    # Generate the query string
    operation["query_string"] = extract_query_string(operation)

    return operation


def extract_operations_from_ast(ast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """
    Extract GraphQL operations from TypeScript AST data.
    Now processes query-definitions files.
    """
    operations = []

    for file_path, file_data in ast_data.items():
        # Check if this is a query definitions file
        if "query-definitions" not in file_path:
            continue

        # Extract from constants in the file
        for const in file_data.get("constants", []):
            const_value = const.get("value", {})

            # Check if this constant contains queries
            if isinstance(const_value, dict) and "queries" in const_value:
                entity = const_value.get("entity", "Unknown")

                # Process each query in the queries array
                for query_def in const_value.get("queries", []):
                    operation = transform_query_to_operation(query_def, entity)
                    if operation:
                        operations.append(operation)

    return operations


def generate_operations_metadata(operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Generate metadata for operations to be used in templates.
    """
    metadata = []
    for op in operations:
        meta = {
            "name": op["name"],
            "type": op["type"],
            "entity": op.get("entity", "Unknown"),
            "has_variables": len(op.get("variables", [])) > 0,
            "variable_count": len(op.get("variables", [])),
            "variable_names": [v["name"] for v in op.get("variables", [])],
            "class_name": f"{op['name']}Operation",
            "query_const_name": f"{op['name'].upper()}_{op['type'].upper()}",
        }
        metadata.append(meta)
    return metadata


def collect_required_imports(operations: list[dict[str, Any]]) -> dict[str, list[str]]:
    """
    Collect required imports based on operations.
    """
    imports = {
        "typing": ["Any", "Dict", "List", "Optional"],
        "strawberry": [],  # For Upload and other Strawberry-specific types
        "domain": [],
    }

    # Check if we need TypedDict for variables
    for op in operations:
        if op.get("variables"):
            imports["typing"].append("TypedDict")
            break

    # Collect unique types from operations
    types_used = set()
    strawberry_types = set()

    # Standard GraphQL scalar types
    standard_scalars = {"String", "Int", "Float", "Boolean", "ID"}
    # Strawberry-specific types that should come from strawberry imports
    strawberry_scalars = {"Upload", "JSON", "DateTime", "Date", "Time", "Decimal"}

    for op in operations:
        # Check variables for types
        for var in op.get("variables", []):
            var_type = var.get("type", "")
            if var_type:
                if var_type in strawberry_scalars:
                    strawberry_types.add(var_type)
                elif var_type not in standard_scalars:
                    types_used.add(var_type)

    # Add strawberry imports for special types
    if strawberry_types:
        imports["strawberry"] = list(strawberry_types)

    # Add domain imports for custom types
    if types_used:
        imports["domain"] = list(types_used)

    return imports


# ============================================================================
# UNIFIED IR BUILDER
# ============================================================================


class UnifiedIRBuilder:
    """Builds unified IR combining operations and domain types."""

    def __init__(self, config: StrawberryConfig):
        self.config = config
        # Create TypeConverter with custom mappings from config
        custom_mappings = {"ts_to_python": config.type_mappings.get("scalar_mappings", {})}
        self.type_converter = TypeConverter(custom_mappings)

    def build_domain_ir(self, ast: dict[str, Any]) -> dict[str, Any]:
        """Extract domain types from AST."""
        ir = {"interfaces": [], "scalars": [], "enums": [], "inputs": [], "node_specs": []}

        # Process enums
        for enum in ast.get("enums", []):
            enum_name = enum.get("name", "")

            # Skip GraphQL infrastructure enums
            if enum_name in ["QueryOperationType", "CrudOperation", "QueryEntity"]:
                continue

            # Skip if it's a field configuration enum
            if enum_name in ["FieldPreset", "FieldGroup"]:
                continue

            ir["enums"].append(
                {
                    "name": enum_name,
                    "values": enum.get("values", enum.get("members", [])),
                    "description": enum.get("description", ""),
                }
            )

        # Process branded scalars (from brandedScalars array)
        for scalar in ast.get("brandedScalars", []):
            ir["scalars"].append(
                {
                    "name": scalar.get("name", ""),
                    "type": scalar.get("baseType", "string"),
                    "description": scalar.get("description", ""),
                }
            )

        # Also check types array for branded types (e.g., string & { __brand: 'NodeID' })
        for type_def in ast.get("types", []):
            type_str = type_def.get("type", "")
            # Check if it's a branded type
            if "__brand" in type_str:
                ir["scalars"].append(
                    {
                        "name": type_def.get("name", ""),
                        "type": "string",  # Branded types are usually strings
                        "description": f"Branded scalar type for {type_def.get('name', '')}",
                    }
                )

        # Process interfaces (domain types)
        for interface in ast.get("interfaces", []):
            interface_name = interface.get("name", "")

            # Skip query/infrastructure interfaces
            skip_patterns = [
                "Query",
                "Input",
                "Variables",
                "Result",
                "Response",
                "Arguments",
                "Params",
                "FieldDefinition",
                "FieldArgument",
                "VariableDefinition",
            ]
            # More specific skip patterns that need exact match or specific context
            exact_skip_patterns = [
                "Config",
                "Options",
            ]  # Only skip if it's exactly "Config" or "Options"

            # Check skip patterns
            should_skip = any(pattern in interface_name for pattern in skip_patterns)
            # Check exact patterns - skip only if the name exactly matches
            should_skip = should_skip or interface_name in exact_skip_patterns

            # Special case: Don't skip PersonLLMConfig (it's a domain type)
            if interface_name == "PersonLLMConfig":
                should_skip = False

            # Special case: Don't skip WebSearchResult and ImageGenerationResult (they're domain types)
            if interface_name in ["WebSearchResult", "ImageGenerationResult"]:
                should_skip = False

            # Special case: Don't skip ExecutionOptions (it's a domain type needed for execution)
            if interface_name == "ExecutionOptions":
                should_skip = False

            if should_skip:
                continue

            # Build properties with Python types
            props = []
            for prop in interface.get("properties", []):
                prop_name = prop.get("name", "")
                prop_type = prop.get("type", "any")

                # Convert to Python type
                py_type = self.type_converter.ts_to_python(prop_type)

                props.append(
                    {
                        "name": prop_name,
                        "type": py_type,
                        "optional": prop.get("optional", prop.get("isOptional", False)),
                        "description": prop.get("description", ""),
                    }
                )

            ir["interfaces"].append(
                {
                    "name": interface_name,
                    "properties": props,
                    "description": interface.get("description", ""),
                }
            )

        # Process input types (from inputs array if present)
        for input_type in ast.get("inputs", []):
            props = []
            for prop in input_type.get("properties", []):
                py_type = self.type_converter.ts_to_python(prop.get("type", "any"))
                props.append(
                    {
                        "name": prop.get("name", ""),
                        "type": py_type,
                        "is_optional": prop.get("optional", prop.get("isOptional", False)),
                        "description": prop.get("description", ""),
                    }
                )

            ir["inputs"].append(
                {
                    "name": input_type.get("name", ""),
                    "fields": props,
                    "description": input_type.get("description", ""),
                }
            )

        # Also process input types from types array (for types ending with "Input")
        for type_def in ast.get("types", []):
            name = type_def.get("name", "")
            # Only process types that end with "Input"
            if name.endswith("Input"):
                type_str = type_def.get("type", "")
                props = []

                # Parse TypeScript type string to extract properties
                # Format: { prop1: Type1; prop2?: Type2; ... }
                if type_str.startswith("{") and type_str.endswith("}"):
                    # Remove outer braces and split by semicolon
                    fields_str = type_str[1:-1].strip()
                    # Split by semicolon but handle nested structures
                    field_lines = [line.strip() for line in fields_str.split(";") if line.strip()]

                    for field_line in field_lines:
                        # Parse each field: name: type or name?: type
                        if ":" in field_line:
                            field_parts = field_line.split(":", 1)
                            field_name = field_parts[0].strip()
                            field_type = field_parts[1].strip()

                            # Check if optional (has ? before colon)
                            optional = field_name.endswith("?")
                            if optional:
                                field_name = field_name[:-1].strip()

                            # Convert TypeScript type to Python type
                            # Handle special cases for Scalars and InputMaybe
                            py_type = field_type

                            # Handle Scalars['Type']['input'] pattern
                            if "Scalars[" in field_type:
                                # Extract the scalar type
                                scalar_match = re.search(r"Scalars\['(\w+)'\]", field_type)
                                if scalar_match:
                                    scalar_type = scalar_match.group(1)
                                    py_type = scalar_type

                            # Handle InputMaybe<Type> pattern
                            if field_type.startswith("InputMaybe<"):
                                optional = True
                                # Extract inner type
                                inner_type = field_type[11:-1]  # Remove InputMaybe< and >
                                # Process inner type
                                if inner_type.startswith("Array<"):
                                    # Handle InputMaybe<Array<Type>>
                                    array_inner = inner_type[6:-1]  # Remove Array< and >
                                    if "Scalars[" in array_inner:
                                        scalar_match = re.search(r"Scalars\['(\w+)'\]", array_inner)
                                        if scalar_match:
                                            py_type = f"List[{scalar_match.group(1)}]"
                                    else:
                                        py_type = f"List[{array_inner}]"
                                elif "Scalars[" in inner_type:
                                    scalar_match = re.search(r"Scalars\['(\w+)'\]", inner_type)
                                    if scalar_match:
                                        py_type = scalar_match.group(1)
                                else:
                                    py_type = inner_type

                            # Handle Array<Type> pattern
                            elif field_type.startswith("Array<"):
                                inner_type = field_type[6:-1]  # Remove Array< and >
                                if "Scalars[" in inner_type:
                                    scalar_match = re.search(r"Scalars\['(\w+)'\]", inner_type)
                                    if scalar_match:
                                        py_type = f"List[{scalar_match.group(1)}]"
                                else:
                                    py_type = f"List[{inner_type}]"

                            # Handle direct enum references
                            elif field_type in [
                                "LLMService",
                                "NodeType",
                                "APIServiceType",
                                "Status",
                                "DiagramFormat",
                                "DiagramFormatGraphQL",
                            ] or field_type.endswith("Input"):
                                py_type = field_type

                            props.append(
                                {
                                    "name": field_name,
                                    "type": py_type,
                                    "is_optional": optional,
                                    "description": "",
                                }
                            )

                # Add to inputs if we found properties
                if props:
                    ir["inputs"].append(
                        {
                            "name": name,
                            "fields": props,
                            "description": type_def.get("description", ""),
                        }
                    )

        # Process node specs from constants if present
        for const in ast.get("constants", []):
            const_name = const.get("name", "")
            # Check for spec constants (could be 'apiJobSpec' or 'apiJobSpecification')
            if const_name.endswith("Spec") or const_name.endswith("Specification"):
                spec_value = const.get("value", {})
                if isinstance(spec_value, dict) and spec_value.get("fields"):
                    node_type = const_name.replace("Specification", "").replace("Spec", "")

                    # Process fields with proper type metadata
                    processed_fields = []
                    for field in spec_value.get("fields", []):
                        field_name = field.get("name", "")
                        field_type = field.get("type", "string")

                        # Map TypeScript field types to Python/GraphQL types
                        python_type = "str"
                        graphql_type = "String"
                        is_enum = False
                        enum_values = []
                        is_object_type = False

                        if field_type == "string":
                            python_type = "str"
                            graphql_type = "String"
                        elif field_type == "number":
                            python_type = "int"
                            graphql_type = "Int"
                        elif field_type == "boolean":
                            python_type = "bool"
                            graphql_type = "Boolean"
                        elif field_type == "object":
                            python_type = "Dict[str, Any]"
                            graphql_type = "JSON"
                            is_object_type = True
                        elif field_type == "array":
                            python_type = "List[Any]"
                            graphql_type = "[JSON]"
                        elif field_type == "enum":
                            # Extract enum values from validation
                            validation = field.get("validation", {})
                            if "allowedValues" in validation:
                                enum_values = validation["allowedValues"]
                                is_enum = True
                                # For enums, use the field name as the type
                                enum_type_name = f"{node_type}{field_name.title()}Enum"
                                python_type = enum_type_name
                                graphql_type = enum_type_name

                        processed_field = {
                            "name": field_name,
                            "type": field_type,  # Original TypeScript type
                            "python_type": python_type,
                            "graphql_type": graphql_type,
                            "required": field.get("required", False),
                            "description": field.get("description", ""),
                            "is_object_type": is_object_type,
                            "is_dict_type": is_object_type,  # For backward compatibility
                            "is_enum": is_enum,
                            "enum_values": enum_values,
                            "validation": field.get("validation", {}),
                            "uiConfig": field.get("uiConfig", {}),
                        }
                        processed_fields.append(processed_field)

                    # Build the complete spec with processed fields
                    node_spec = {
                        "name": node_type,
                        "spec": {
                            "nodeType": spec_value.get("nodeType"),
                            "displayName": spec_value.get("displayName", node_type),
                            "category": spec_value.get("category", ""),
                            "description": spec_value.get("description", ""),
                            "icon": spec_value.get("icon", ""),
                            "color": spec_value.get("color", ""),
                            "fields": processed_fields,
                            "handles": spec_value.get("handles", {}),
                            "outputs": spec_value.get("outputs", {}),
                            "execution": spec_value.get("execution", {}),
                            "primaryDisplayField": spec_value.get("primaryDisplayField", ""),
                        },
                    }
                    ir["node_specs"].append(node_spec)

        return ir

    def build_operations_ir(self, operations_meta: list[dict[str, Any]]) -> dict[str, Any]:
        """Build operations intermediate representation."""
        return {
            "queries": [op for op in operations_meta if op["type"] == "query"],
            "mutations": [op for op in operations_meta if op["type"] == "mutation"],
            "subscriptions": [op for op in operations_meta if op["type"] == "subscription"],
        }

    def generate_result_wrappers(self, ops_ir: dict[str, Any]) -> list[dict[str, Any]]:
        """Generate result wrapper types for operations."""
        wrappers = []

        # Process all operation types
        for op_type in ["queries", "mutations", "subscriptions"]:
            for op in ops_ir.get(op_type, []):
                wrapper = {
                    "name": f"{op['name']}Result",
                    "operation": op["name"],
                    "type": op_type.rstrip("s"),  # Remove plural 's'
                    "fields": [],  # Will be populated by templates
                }
                wrappers.append(wrapper)

        return wrappers

    def process_types_for_strawberry(
        self, interfaces: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Process domain types for Strawberry GraphQL generation using type resolver."""
        # Initialize type resolver with config
        config_path = self.config.root / "type_annotations.yaml"
        resolver = StrawberryTypeResolver(config_path)
        types = []

        # Process each interface with type resolver

        for interface in interfaces:
            interface_name = interface["name"]

            # Resolve all fields using the type resolver
            resolved_fields = []
            for prop in interface.get("properties", []):
                field_data = {
                    "name": prop["name"],
                    "type": prop["type"],
                    "optional": prop.get("optional", prop.get("isOptional", False)),
                    "description": prop.get("description", ""),
                }
                resolved_field = resolver.resolve_field(field_data, interface_name)
                resolved_fields.append(resolved_field)

            # Generate conversion method if needed
            conversion_method = resolver.generate_conversion_method(interface_name, resolved_fields)

            # Determine if this type can use the pydantic decorator
            can_use_pydantic_decorator = interface_name in resolver.PYDANTIC_DECORATOR_TYPES

            # Build the type structure for templates
            strawberry_type = {
                "name": interface_name,
                "fields": [],  # Keep original fields for backward compatibility
                "resolved_fields": [  # Add resolved fields for new template
                    {
                        "name": f.name,
                        "strawberry_type": f.strawberry_type,
                        "default": f.default,
                        "python_type": f.python_type,
                        "is_optional": f.is_optional,
                        "is_json": f.is_json,
                        "is_literal": f.is_literal,
                        "is_custom_list": f.is_custom_list,
                        "needs_conversion": f.needs_conversion,
                        "conversion_expr": f.conversion_expr,
                    }
                    for f in resolved_fields
                ],
                "description": interface.get("description", ""),
                "needs_manual_conversion": conversion_method.needs_method,
                "conversion_method": conversion_method.method_code,
                "can_use_pydantic_decorator": can_use_pydantic_decorator,
                "has_json_dict": any(f.is_json for f in resolved_fields),
                "has_literal": any(f.is_literal for f in resolved_fields),
                "has_custom_lists": any(f.is_custom_list for f in resolved_fields),
            }

            # Also populate original fields for backward compatibility
            for prop in interface.get("properties", []):
                field = {
                    "name": prop["name"],
                    "type": prop["type"],
                    "optional": prop.get("optional", prop.get("isOptional", False)),
                    "description": prop.get("description", ""),
                    "is_json_dict": "JsonDict" in prop["type"] or "JsonValue" in prop["type"],
                    "is_literal": prop["type"].startswith("'") or "Union['" in prop["type"],
                    "is_custom_list": prop["type"].startswith("List[") and "Domain" in prop["type"],
                }
                strawberry_type["fields"].append(field)

            types.append(strawberry_type)

        return types

    def build_template_operations(self, operations: list[dict[str, Any]]) -> dict[str, Any]:
        """Build operations formatted for schema templates."""
        template_ops = {"queries": [], "mutations": [], "subscriptions": []}

        for op in operations:
            op_type = op["type"]

            # Build template operation with the field names the template expects
            template_op = {
                "operation_name": op["name"],
                "operation_type": op_type,
                "parameters": self._build_parameters(op.get("variables", [])),
                "description": f"{op['type'].title()} for {op.get('entity', 'unknown')}",
                # Optional alias_name for GraphQL field naming
                "alias_name": None,  # Will be set below for specific cases
            }

            # For queries, we might want to use a different field name
            # to follow GraphQL conventions (noun instead of verb)
            if op_type == "query":
                # Transform verb-based query names to nouns if needed
                if op["name"].startswith("Get"):
                    # GetExecution → execution, GetApiKeys → api_keys
                    field_name = op["name"][3:]  # Remove "Get"
                    if field_name.endswith("s"):
                        # GetApiKeys → api_keys
                        template_op["alias_name"] = self._to_snake_case(field_name)
                    else:
                        # GetExecution → execution
                        template_op["alias_name"] = self._to_snake_case(field_name)
                elif op["name"].startswith("List"):
                    # ListExecutions → executions
                    template_op["alias_name"] = self._to_snake_case(op["name"][4:])
                elif op["name"].startswith("Search"):
                    # SearchDiagrams → search_diagrams
                    template_op["alias_name"] = self._to_snake_case(op["name"])
                else:
                    template_op["alias_name"] = self._to_snake_case(op["name"])

            # Add to appropriate list
            if op_type == "query":
                template_ops["queries"].append(template_op)
            elif op_type == "mutation":
                template_ops["mutations"].append(template_op)
            elif op_type == "subscription":
                template_ops["subscriptions"].append(template_op)

        return template_ops

    def _to_snake_case(self, name: str) -> str:
        """Convert PascalCase to snake_case."""
        import re

        s1 = re.sub("(.)([A-Z][a-z]+)", r"\1_\2", name)
        return re.sub("([a-z0-9])([A-Z])", r"\1_\2", s1).lower()

    def _get_return_type(self, operation: dict[str, Any]) -> str:
        """Determine return type for an operation."""
        # This is simplified - you might want more complex logic
        entity = operation.get("entity", "Any")
        if operation["name"].startswith("Get") or operation["name"].startswith("List"):
            if "s" in operation["name"][-2:]:  # Plural
                return f"list[{entity}]"
            return entity
        return "Any"

    def _build_parameters(self, variables: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Build parameter list for schema templates."""
        params = []
        for var in variables:
            param = {
                "name": var["name"],
                "type": self._map_graphql_type(var.get("graphql_type", var["type"])),
                "optional": not var.get("required", False),  # Template expects 'optional' field
                "needs_conversion": True,  # Flag for template to handle type conversion
            }
            params.append(param)
        return params

    def _map_graphql_type(self, graphql_type: str) -> str:
        """Map GraphQL type to Python type."""
        type_map = {"String": "str", "Int": "int", "Float": "float", "Boolean": "bool", "ID": "str"}
        return type_map.get(graphql_type, graphql_type)


# ============================================================================
# STRAWBERRY IR BUILDER CLASS
# ============================================================================


class StrawberryIRBuilder(BaseIRBuilder):
    """Build IR for GraphQL/Strawberry code generation."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize strawberry IR builder.

        Args:
            config_path: Optional path to configuration file
        """
        super().__init__(config_path or "projects/codegen/config/strawberry")
        self.base_dir = Path(os.environ.get("DIPEO_BASE_DIR", "/home/soryhyun/DiPeO"))

    async def build_ir(
        self, source_data: dict[str, Any], config: Optional[dict[str, Any]] = None
    ) -> IRData:
        """Build IR from source data.

        Args:
            source_data: Input AST data to build IR from
            config: Optional configuration parameters

        Returns:
            IRData containing the built strawberry IR
        """
        # 1. Load configuration
        config_path = self.base_dir / "projects/codegen/config/strawberry"
        config_obj = StrawberryConfig(config_path)

        # Create builder instance
        builder = UnifiedIRBuilder(config_obj)

        # 2. Handle input data - the db node always wraps in 'default' key
        if "default" in source_data:
            file_dict = source_data.get("default", {})
        else:
            file_dict = source_data

        # Files to exclude from domain type generation
        exclude_patterns = [
            "ast-types.ts",  # AST parsing types
            "query-specifications.ts",  # Frontend query types
            "relationship-queries.ts",  # Frontend relationship configs
            "query-types.ts",  # Query building infrastructure types (FieldArgument, etc.)
            "graphql-types.ts",  # Frontend GraphQL type definitions
            # Note: We DON'T exclude query-definitions/* because those contain actual operations
        ]

        # 3. Merge all AST files into a single structure
        merged_ast = {
            "interfaces": [],
            "enums": [],
            "brandedScalars": [],
            "inputs": [],
            "types": [],  # Add types array
            "constants": [],  # Add constants array for node specs
        }

        # Each key is a file path, each value is the AST content
        for file_path, ast_content in file_dict.items():
            # Skip files that should be excluded from domain types
            if any(pattern in file_path for pattern in exclude_patterns):
                continue

            if isinstance(ast_content, dict):
                # Merge content into merged_ast
                if "interfaces" in ast_content:
                    merged_ast["interfaces"].extend(ast_content["interfaces"])
                if "enums" in ast_content:
                    merged_ast["enums"].extend(ast_content["enums"])
                if "brandedScalars" in ast_content:
                    merged_ast["brandedScalars"].extend(ast_content["brandedScalars"])
                if "inputs" in ast_content:
                    merged_ast["inputs"].extend(ast_content["inputs"])
                if "types" in ast_content:
                    merged_ast["types"].extend(ast_content["types"])
                if "constants" in ast_content:
                    merged_ast["constants"].extend(ast_content["constants"])
            elif isinstance(ast_content, list):
                # Handle list format (shouldn't typically happen)
                for item in ast_content:
                    if isinstance(item, dict):
                        if "interfaces" in item:
                            merged_ast["interfaces"].extend(item["interfaces"])
                        # ... (same for other fields)

        # 4. Extract operations from AST
        # logger.info(f"Processing {len(file_dict)} AST files")
        operations = extract_operations_from_ast(file_dict)
        # logger.info(f"Extracted {len(operations)} operations")

        # Group operations by type
        queries = [op for op in operations if op["type"] == "query"]
        mutations = [op for op in operations if op["type"] == "mutation"]
        subscriptions = [op for op in operations if op["type"] == "subscription"]

        # Generate operations metadata
        operations_metadata = generate_operations_metadata(operations)

        # Collect required imports
        imports = collect_required_imports(operations)

        domain_ir = builder.build_domain_ir(merged_ast)

        # 6. Build operations IR
        ops_ir = builder.build_operations_ir(operations_metadata)

        # 7. Generate result wrappers
        result_wrappers = builder.generate_result_wrappers(ops_ir)

        # 8. Process types for Strawberry
        strawberry_types = builder.process_types_for_strawberry(domain_ir["interfaces"])

        # 9. Build template operations (for generated_schema.py)
        template_operations = builder.build_template_operations(operations)

        # 10. Build complete unified IR
        ir_dict = {
            "version": 1,
            "generated_at": datetime.now().isoformat(),
            # Domain types
            "interfaces": domain_ir["interfaces"],
            "scalars": domain_ir["scalars"],
            "enums": domain_ir["enums"],
            "inputs": domain_ir["inputs"],
            "node_specs": domain_ir.get("node_specs", []),
            # Operations data (for operations.py generation - raw format)
            "operations": operations,
            "imports": imports,
            # Keep original operation lists for operations.py template
            "raw_queries": queries,
            "raw_mutations": mutations,
            "raw_subscriptions": subscriptions,
            # Template operations (for generated_schema.py template - formatted)
            "queries": template_operations["queries"],
            "mutations": template_operations["mutations"],
            "subscriptions": template_operations["subscriptions"],
            # Operations IR (for schema generation)
            "operations_ir": ops_ir,
            "result_wrappers": result_wrappers,
            # Strawberry types
            "types": strawberry_types,
            # Configuration
            "config": config_obj.to_dict(),
            # Statistics for templates - using 'metadata' name for backward compatibility
            # This will be preserved during IR builder handler processing
            "metadata": {
                "ast_file_count": len(file_dict),
                "interface_count": len(domain_ir["interfaces"]),
                "enum_count": len(domain_ir["enums"]),
                "scalar_count": len(domain_ir["scalars"]),
                "input_count": len(domain_ir["inputs"]),
                "node_spec_count": len(domain_ir.get("node_specs", [])),
                "total_operations": len(operations),
                "total_queries": len(queries),
                "total_mutations": len(mutations),
                "total_subscriptions": len(subscriptions),
                "operations_meta": operations_metadata,  # Include for compatibility
            },
        }

        # 11. Write unified IR to file for debugging/inspection
        ir_output_path = self.base_dir / "projects/codegen/ir/strawberry_ir.json"
        ir_output_path.parent.mkdir(parents=True, exist_ok=True)
        ir_output_path.write_text(json.dumps(ir_dict, indent=2))
        logger.info(f"Wrote unified IR to {ir_output_path}")

        # Create metadata
        metadata = self.create_metadata(source_data, "strawberry")

        # Return wrapped IR data
        return IRData(metadata=metadata, data=ir_dict)

    def validate_ir(self, ir_data: IRData) -> bool:
        """Validate strawberry IR structure.

        Args:
            ir_data: IR data to validate

        Returns:
            True if valid, False otherwise
        """
        if not super().validate_ir(ir_data):
            return False

        # Check for required strawberry fields
        # Note: Updated to match actual IR structure from strawberry_ir_builder.py
        data = ir_data.data
        required_keys = ["operations", "scalars", "types", "inputs", "enums"]
        # Also accept alternative keys for backward compatibility
        alternative_keys = {
            "types": "domain_types",  # types or domain_types
            "result_wrappers": "results",  # result_wrappers or results
        }

        for key in required_keys:
            if key not in data:
                # Check if alternative key exists
                alt_key = alternative_keys.get(key)
                if (alt_key and alt_key not in data) or not alt_key:
                    return False

        # Validate operations have required fields
        operations = data.get("operations", [])
        if not isinstance(operations, list):
            return False

        return True
