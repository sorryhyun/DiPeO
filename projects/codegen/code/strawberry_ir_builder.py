"""
Unified IR Builder for Strawberry Code Generation
Combines operations extraction and domain IR building into a single module
to eliminate circular dependencies and create a single source of truth.
"""

from __future__ import annotations
from pathlib import Path
import json
import re
from typing import Any, Dict, List, Optional
from datetime import datetime
import yaml
import sys
import os

# Add the DiPeO base directory to path for imports
sys.path.append(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))


# ============================================================================
# SHARED UTILITIES
# ============================================================================

class TypeMapper:
    """Maps TypeScript types to Python types for GraphQL generation."""

    def __init__(self, cfg):
        self.cfg = cfg

    def ts_to_py(self, ts: str) -> str:
        s = ts.strip()
        # branded scalars
        m = re.search(r"string\s*&\s*{[^']*'__brand':\s*'([^']+)'}", s)
        if m:
            return f"{m.group(1)}"  # NodeID, DiagramID, etc. (handled as scalars)
        # scalar map
        scalars = self.cfg.type_mappings.get("scalar_mappings", {})
        if s in scalars: return scalars[s]
        # collections / records
        if "Record<" in s or "Dict" in s: return "JSONScalar"
        if s.startswith("Array<"): return f"list[{self.ts_to_py(s[6:-1])}]"
        # fall back
        return s


# NOTE: Type conversion functions moved to template filters
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

    def _load(self, name: str) -> Dict[str, Any]:
        with open(self.root / name, "r") as f:
            return yaml.safe_load(f) or {}

    def _opt(self, name: str) -> Dict[str, Any]:
        p = self.root / name
        return self._load(name) if p.exists() else {}

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization"""
        return {
            "type_mappings": self.type_mappings,
            "domain_fields": self.domain_fields,
            "schema": self.schema
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
    type_value = query_data.get('type', 'query')
    if '.' in type_value:
        operation_type = type_value.split('.')[-1].lower()
    else:
        operation_type = type_value.lower()

    name = query_data.get('name', 'UnknownOperation')
    variables = query_data.get('variables', [])
    fields = query_data.get('fields', [])

    # Build variable declarations
    var_declarations = []
    for var in variables:
        var_name = var.get('name', '')
        var_type = var.get('type', 'String')
        # Convert ID type to String for GraphQL compatibility
        if var_type == 'ID':
            var_type = 'String'
        required = var.get('required', False)
        var_declarations.append(f"${var_name}: {var_type}{'!' if required else ''}")

    # Build query string
    if var_declarations:
        query_str = f"{operation_type} {name}({', '.join(var_declarations)}) {{\n"
    else:
        query_str = f"{operation_type} {name} {{\n"

    # Add fields - transform to noun form for queries
    for field in fields:
        query_str += build_field_string(field, indent=1, operation_type=operation_type, operation_name=name)

    query_str += "}"

    return query_str


def build_field_string(field: dict[str, Any], indent: int = 0, operation_type: str = None, operation_name: str = None) -> str:
    """
    Build GraphQL field string with proper indentation.
    For queries, transforms verb forms to noun forms.
    """
    # Handle case where field might be a string after const resolution
    if isinstance(field, str):
        # If it's just a string, treat it as a field name
        return f"{'  ' * indent}{field}\n"

    # Ensure field is a dictionary
    if not isinstance(field, dict):
        # Skip non-dict fields
        return ""

    indent_str = "  " * indent
    field_name = field.get('name', '')

    # Transform field name to noun form for queries at the root level
    if operation_type == 'query' and indent == 1 and field_name:
        # Convert verb form to noun form for root query fields
        field_name = transform_query_field_to_noun(field_name)

    field_str = f"{indent_str}{field_name}"

    # Add arguments if present
    args = field.get('args', [])
    if args:
        arg_strs = []
        for arg in args:
            arg_name = arg.get('name', '')
            is_variable = arg.get('isVariable', False)
            arg_value = arg.get('value', '')
            if is_variable:
                arg_strs.append(f"{arg_name}: ${arg_value}")
            else:
                # Handle literal values
                if isinstance(arg_value, str) and not arg_value.startswith('$'):
                    arg_strs.append(f'{arg_name}: "{arg_value}"')
                else:
                    arg_strs.append(f"{arg_name}: {arg_value}")
        field_str += f"({', '.join(arg_strs)})"

    # Add nested fields if present
    nested_fields = field.get('fields', [])
    if nested_fields:
        # Check if nested_fields is a string (unresolved const reference)
        if isinstance(nested_fields, str):
            # This is an unresolved const reference, skip it or treat as empty
            field_str += " {\n"
            field_str += f"{indent_str}  # ERROR: Unresolved const reference: {nested_fields}\n"
            field_str += f"{indent_str}}}\n"
        elif isinstance(nested_fields, list):
            field_str += " {\n"
            for nested_field in nested_fields:
                # Pass operation info to nested fields but increment indent to avoid transformation
                field_str += build_field_string(nested_field, indent + 1, operation_type, operation_name)
            field_str += f"{indent_str}}}\n"
        else:
            field_str += "\n"
    else:
        field_str += "\n"

    return field_str


def transform_query_field_to_noun(field_name: str) -> str:
    """
    Transform query field names from verb form to noun form.
    Handles both camelCase and snake_case inputs.
    e.g., getExecution -> execution, get_execution -> execution, listDiagrams -> diagrams
    """
    import re

    # Handle snake_case input (e.g., get_execution -> execution)
    if field_name.startswith('get_'):
        # get_execution -> execution
        return field_name[4:]
    elif field_name.startswith('list_'):
        # list_diagrams -> diagrams (already plural in most cases)
        base = field_name[5:]
        # Simple pluralization if not already plural
        if not base.endswith('s'):
            if base.endswith('y'):
                return base[:-1] + 'ies'
            else:
                return base + 's'
        return base

    # Handle camelCase input (e.g., getExecution -> execution)
    elif field_name.startswith('get'):
        # getExecution -> execution
        base = field_name[3:]
        # Convert first letter to lowercase
        if base:
            base = base[0].lower() + base[1:]
        # Convert to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', base)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    # Handle list* camelCase -> remove "list" prefix and make plural
    elif field_name.startswith('list'):
        # listDiagrams -> diagrams
        base = field_name[4:]
        # Convert first letter to lowercase
        if base:
            base = base[0].lower() + base[1:]
        # Convert to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', base)
        snake_base = re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

        # Simple pluralization
        if snake_base.endswith('s'):
            return snake_base + 'es'
        elif snake_base.endswith('y'):
            return snake_base[:-1] + 'ies'
        else:
            return snake_base + 's'

    # For other queries, just convert to snake_case if needed
    else:
        # If already snake_case, return as is
        if '_' in field_name:
            return field_name
        # Convert camelCase to snake_case
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', field_name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()


def transform_query_to_operation(query_data: dict[str, Any], entity: str) -> Optional[dict[str, Any]]:
    """
    Transform a TypeScript query definition to Python operation format.
    """
    if not query_data:
        return None

    name = query_data.get('name', '')
    if not name:
        return None

    # Extract operation type from enum value (e.g., "QueryOperationType.QUERY" -> "query")
    type_value = query_data.get('type', 'query')
    if '.' in type_value:
        operation_type = type_value.split('.')[-1].lower()
    else:
        operation_type = type_value.lower()

    variables = query_data.get('variables', [])
    fields = query_data.get('fields', [])

    # Generate the GraphQL query string
    query_string = extract_query_string(query_data)

    # Transform variables to Python format
    python_variables = []
    for var in variables:
        var_name = var.get('name', '')
        var_type = var.get('type', 'String')
        required = var.get('required', False)
        # Keep raw GraphQL type - template will convert
        python_type = var_type

        # Generate union type for variables that could be Strawberry input objects
        clean_type = var_type.replace('[', '').replace(']', '').replace('!', '')

        # For mutation inputs, don't use Union types - GraphQL doesn't support them
        # Just use the direct input type
        if clean_type.endswith('Input'):
            # For custom input types, use direct type (no Union)
            if required:
                union_type = clean_type
            else:
                union_type = f"Optional[{clean_type}]"
        elif clean_type == 'Upload':
            # Special handling for file upload type
            if required:
                union_type = 'Upload'
            else:
                union_type = 'Optional[Upload]'
        else:
            # For non-input types, let template handle conversion
            union_type = None  # Template will use python_type with filter

        python_variables.append({
            'name': var_name,
            'graphql_type': var_type,
            'python_type': python_type,
            'union_type': union_type,
            'required': required
        })

    # Generate constant name and class name (template will handle casing)
    const_name = f"{name}_{operation_type.upper()}"
    class_name = f"{name}Operation"

    return {
        'name': name,
        'entity': entity,
        'type': operation_type,
        'const_name': const_name,
        'class_name': class_name,
        'query_string': query_string,
        'variables': python_variables,
        'has_variables': len(python_variables) > 0,
        'fields': fields
    }


def extract_operations_from_ast(ast_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Extract all operations from TypeScript AST data.
    """
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

    return operations


def generate_operations_metadata(operations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Generate operations metadata for the IR.
    """
    metadata = []

    for op in operations:
        # Extract the first word (verb) from operation name
        # e.g., CreateDiagram -> create, UpdateNode -> update
        operation_verb = ''
        op_name = op['name']
        if op_name:
            # Split on capital letters to get first word
            import re
            words = re.findall(r'[A-Z][a-z]*', op_name)
            if words:
                operation_verb = words[0].lower()

        meta = {
            "name": op['name'],
            "kind": op['type'],  # query, mutation, subscription
            # Return type will be determined by template filters
            "variables": [],
            "operation": operation_verb  # Add the operation verb (create, update, delete, etc.)
        }

        # Add variable metadata
        for var in op.get('variables', []):
            var_meta = {
                "name": var.get('name', ''),
                "type": var.get('graphql_type', 'String'),
                "required": var.get('required', False)
            }
            meta["variables"].append(var_meta)

        # Add description if available
        if 'description' in op:
            meta["description"] = op['description']

        metadata.append(meta)

    return metadata


def collect_required_imports(operations: list[dict[str, Any]]) -> dict[str, list[str]]:
    """
    Collect all required imports based on operations.
    """
    imports = {
        'typing': set(),
        'dipeo.diagram_generated.graphql.inputs': set(),
        'dipeo.diagram_generated.enums': set(),
        'strawberry.file_uploads': set(),
    }

    # Always need these
    imports['typing'].add('Any')
    imports['typing'].add('Optional')
    imports['typing'].add('TypedDict')
    # Remove Union since we're not using it anymore for inputs

    # Check for custom types in variables
    for operation in operations:
        for var in operation.get('variables', []):
            graphql_type = var.get('graphql_type', '')
            # Remove array brackets and required markers
            clean_type = graphql_type.replace('[', '').replace(']', '').replace('!', '')

            # Check if it's a custom input type
            if clean_type.endswith('Input'):
                imports['dipeo.diagram_generated.graphql.inputs'].add(clean_type)
            elif clean_type == 'Upload':
                # File upload type
                imports['strawberry.file_uploads'].add('Upload')
            elif clean_type == 'DateTime':
                # DateTime is represented as str in Python
                continue
            elif clean_type == 'DiagramFormat' or clean_type == 'DiagramFormatGraphQL':
                # DiagramFormatGraphQL is handled by template with relative import
                continue
            elif clean_type not in ['ID', 'String', 'Int', 'Float', 'Boolean', 'JSON']:
                # Other custom types might be enums too
                imports['dipeo.diagram_generated.enums'].add(clean_type)

    # Convert sets to sorted lists for JSON serialization
    imports = {k: sorted(list(v)) for k, v in imports.items() if v}

    return imports


# ============================================================================
# DOMAIN IR BUILDING
# ============================================================================

class UnifiedIRBuilder:
    """Unified IR builder that combines operations and domain IR generation."""

    def __init__(self, config: StrawberryConfig):
        self.config = config
        self.mapper = TypeMapper(config)

    def to_snake_case(self, name: str) -> str:
        """Convert CamelCase to snake_case."""
        import re
        # Insert underscore before capital letters (except at the start)
        s1 = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        # Insert underscore before capital letter sequences
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', s1).lower()

    def build_domain_ir(self, ast_data: Dict) -> Dict:
        """Extract interfaces, scalars, enums, and node specifications from TypeScript AST"""
        domain_ir = {
            "interfaces": [],
            "scalars": [],
            "enums": [],
            "inputs": [],
            "node_specs": []
        }

        # Query infrastructure interfaces to skip
        query_infrastructure_types = {
            'FieldArgument', 'FieldDefinition', 'VariableDefinition',
            'QueryDefinition', 'EntityQueryDefinitions', 'QueryField',
            'QuerySpecification', 'QueryVariable'
        }

        # Extract interfaces
        for interface in ast_data.get("interfaces", []):
            interface_name = interface["name"]

            # Skip query infrastructure types
            if interface_name in query_infrastructure_types:
                continue

            # Check if this interface has special configuration
            interface_config = self.config.domain_fields.get("interfaces", {}).get(interface_name, {})

            interface_def = {
                "name": interface_name,
                "fields": [],
                "field_methods": interface_config.get("field_methods", []),
                "simple_fields": interface_config.get("simple_fields", True),
                "custom_fields": interface_config.get("custom_fields", []),
                "has_all_fields": interface_config.get("has_all_fields", False)
            }

            # Process fields from AST
            for prop in interface.get("properties", []):
                field = {
                    "name": prop["name"],
                    "type": self.mapper.ts_to_py(prop.get("type", "any")),
                    "is_optional": prop.get("isOptional", False),
                    "description": prop.get("description", "")
                }
                interface_def["fields"].append(field)

            domain_ir["interfaces"].append(interface_def)

        # Extract enums
        # Frontend-only enums that should be skipped for Python/GraphQL generation
        frontend_only_enums = {
            'QueryOperationType', 'CrudOperation', 'QueryEntity',
            'FieldPreset', 'FieldGroup'
        }

        for enum in ast_data.get("enums", []):
            enum_name = enum["name"]

            # Skip frontend-only enums
            if enum_name in frontend_only_enums:
                continue

            # Handle both 'values' and 'members' field names
            enum_values = []

            if "members" in enum:
                # For enums with members (name/value pairs)
                for member in enum.get("members", []):
                    # Create a dict with both name and value
                    enum_values.append({
                        "name": member["name"],
                        "value": member.get("value", member["name"].lower())
                    })
            elif "values" in enum:
                # For simple enum values (just strings)
                for value in enum.get("values", []):
                    if isinstance(value, str):
                        enum_values.append({
                            "name": value,
                            "value": value.lower()
                        })
                    elif isinstance(value, dict):
                        enum_values.append(value)

            enum_def = {
                "name": enum_name,
                "values": enum_values
            }
            domain_ir["enums"].append(enum_def)

        # Extract branded scalars
        for scalar in ast_data.get("brandedScalars", []):
            scalar_def = {
                "name": scalar["brand"],
                "base_type": "strawberry.ID" if "ID" in scalar["brand"] else "str"
            }
            domain_ir["scalars"].append(scalar_def)

        # Also extract scalars from types array (for graphql-inputs.ts format)
        for type_def in ast_data.get("types", []):
            if not isinstance(type_def, dict):
                continue

            name = type_def.get("name", "")

            # Check if it's the Scalars type definition
            if name == "Scalars" and isinstance(type_def.get("type"), str):
                # Parse scalar definitions from the type string
                type_str = type_def["type"]
                # Match patterns like "ApiKeyID: { input: ApiKeyID; output: ApiKeyID; }"
                # Updated pattern to match any word ending with ID (not just starting with word chars)
                scalar_pattern = r'(\w+ID):\s*\{[^}]+\}'
                for match in re.finditer(scalar_pattern, type_str):
                    scalar_name = match.group(1)
                    # Skip base ID but include TaskID and HookID
                    if scalar_name != "ID":
                        scalar_def = {
                            "name": scalar_name,
                            "base_type": "strawberry.ID"
                        }
                        # Avoid duplicates
                        if not any(s["name"] == scalar_name for s in domain_ir["scalars"]):
                            domain_ir["scalars"].append(scalar_def)

            # Check if it's an input type (ends with "Input")
            elif name.endswith("Input") and isinstance(type_def.get("type"), str):
                # Parse the TypeScript type definition to extract fields
                type_str = type_def["type"]
                input_def = {
                    "name": name,
                    "fields": []
                }

                # Parse fields from the type string
                # Match patterns like "field_name: Type" or "field_name?: Type"
                field_pattern = r'(\w+)(\?)?:\s*([^;]+);'
                for match in re.finditer(field_pattern, type_str):
                    field_name = match.group(1)
                    is_optional = match.group(2) == '?'
                    field_type = match.group(3).strip()

                    field_def = {
                        "name": field_name,
                        "type": field_type,  # Keep raw TypeScript type
                        "is_required": not is_optional,
                        "is_optional": is_optional,
                        "description": ""
                    }
                    input_def["fields"].append(field_def)

                if input_def["fields"]:  # Only add if we found fields
                    domain_ir["inputs"].append(input_def)

        # Extract input types from inputs array (original format)
        for input_type in ast_data.get("inputs", []):
            # Skip if not a dict (could be malformed data)
            if not isinstance(input_type, dict):
                continue

            input_def = {
                "name": input_type.get("name", "UnknownInput"),
                "fields": []
            }

            for field in input_type.get("fields", []):
                if not isinstance(field, dict):
                    continue

                field_def = {
                    "name": field.get("name", "unknown"),
                    "type": self.mapper.ts_to_py(field.get("type", "any")),
                    "is_required": field.get("isRequired", False),
                    "description": field.get("description", "")
                }
                input_def["fields"].append(field_def)

            domain_ir["inputs"].append(input_def)

        # Extract node specifications from constants
        for constant in ast_data.get("constants", []):
            if not isinstance(constant, dict):
                continue

            # Check if it's a NodeSpecification constant
            if constant.get("type") == "NodeSpecification" and "value" in constant:
                spec = constant["value"]
                if not isinstance(spec, dict):
                    continue

                # Extract node type and convert to class name
                node_type = spec.get("nodeType", "")
                # Convert "NodeType.API_JOB" to "ApiJob"
                if node_type.startswith("NodeType."):
                    type_name = node_type.replace("NodeType.", "")
                    # Convert SNAKE_CASE to PascalCase
                    parts = type_name.split("_")
                    class_name = "".join(part.capitalize() for part in parts)
                else:
                    class_name = node_type

                # Build node spec definition
                node_spec_def = {
                    "class_name": class_name,
                    "display_name": spec.get("displayName", class_name),
                    "pydantic_model": class_name,
                    "description": spec.get("description", ""),
                    "category": spec.get("category", ""),
                    "icon": spec.get("icon", ""),
                    "color": spec.get("color", ""),
                    "fields": []
                }

                # Process node fields
                for field in spec.get("fields", []):
                    if not isinstance(field, dict):
                        continue

                    # Determine if field is dict type
                    field_type = field.get("type", "string")
                    is_dict_type = field_type in ["object", "dict", "Record", "Dict"]

                    field_def = {
                        "name": field.get("name", ""),
                        "type": self.mapper.ts_to_py(field_type),
                        "required": field.get("required", False),
                        "is_dict_type": is_dict_type,
                        "description": field.get("description", "")
                    }
                    node_spec_def["fields"].append(field_def)

                domain_ir["node_specs"].append(node_spec_def)

        return domain_ir

    def build_operations_ir(self, ops_meta: List[Dict]) -> Dict:
        """Build operations IR from metadata"""
        operations_ir = {
            "queries": [],
            "mutations": [],
            "subscriptions": []
        }

        for op in ops_meta:
            operation_def = {
                "name": op["name"],
                "kind": op.get("kind", "query"),  # Include operation type for template filters
                "variables": op.get("variables", []),
                "description": op.get("description", ""),
                "operation": op.get("operation", "")  # Include the operation verb
            }

            # Categorize by operation type
            if op["kind"] == "query":
                operations_ir["queries"].append(operation_def)
            elif op["kind"] == "mutation":
                operations_ir["mutations"].append(operation_def)
            elif op["kind"] == "subscription":
                operations_ir["subscriptions"].append(operation_def)

        return operations_ir

    def build_template_operations(self, operations: List[Dict]) -> Dict:
        """Transform operations for template consumption"""
        template_ops = {
            "queries": [],
            "mutations": [],
            "subscriptions": []
        }

        for op in operations:
            # Pass raw name - template will handle conversion
            field_name = op['name']

            # Build parameters list
            parameters = []
            for var in op.get('variables', []):
                # Use union_type for inputs, otherwise use raw GraphQL type for template to convert
                param_type = var.get('union_type')
                if not param_type:
                    # Not an input type, use raw GraphQL type (template will convert)
                    param_type = var.get('graphql_type', var.get('python_type', 'Any'))

                param = {
                    'name': var['name'],
                    'type': param_type,
                    'optional': not var.get('required', False),
                    'needs_conversion': not var.get('union_type')  # Flag for template
                }
                parameters.append(param)

            # Build operation definition for template
            # Generate alias name for queries (noun form without prefix)
            alias_name = None
            if op['type'] == 'query':
                # Convert GetExecution -> execution, ListDiagrams -> diagrams
                name = op['name']
                if name.startswith('Get'):
                    # GetExecution -> execution
                    alias_name = self.to_snake_case(name[3:])
                elif name.startswith('List'):
                    # ListDiagrams -> diagrams (already plural, just convert to snake_case)
                    base = name[4:]
                    alias_name = self.to_snake_case(base)
                else:
                    # For other queries, just use snake_case of the full name
                    alias_name = self.to_snake_case(name)

            template_op = {
                'field_name': field_name,  # Raw name - template will convert to snake_case
                'operation_name': op['name'],
                'operation_class': op.get('class_name', f"{op['name']}Operation"),
                'parameters': parameters,
                'operation_type': op['type'],  # Pass type for return type determination
                'description': f"{op['name']} operation",
                'alias_name': alias_name  # Noun form for queries
            }

            # Categorize by type
            if op['type'] == 'query':
                template_ops['queries'].append(template_op)
            elif op['type'] == 'mutation':
                template_ops['mutations'].append(template_op)
            elif op['type'] == 'subscription':
                template_ops['subscriptions'].append(template_op)

        return template_ops

    def generate_result_wrappers(self, ops_ir: Dict) -> List[Dict]:
        """Generate result wrapper types for mutations"""
        wrappers = set()

        # Collect wrapper types based on mutation names
        for mutation in ops_ir.get("mutations", []):
            operation_name = mutation.get("name", "")
            # Determine wrapper type based on operation name patterns
            if operation_name in ['ExecuteDiagram', 'UpdateNodeState', 'ControlExecution', 'SendInteractiveResponse']:
                wrappers.add('ExecutionResult')
            elif operation_name in ['CreateDiagram', 'UpdateDiagram', 'LoadDiagram', 'SaveDiagram']:
                wrappers.add('DiagramResult')
            elif operation_name in ['DeleteDiagram', 'DeleteNode', 'DeletePerson', 'DeleteApiKey']:
                wrappers.add('DeleteResult')
            elif operation_name in ['CreateNode', 'UpdateNode']:
                wrappers.add('NodeResult')
            elif operation_name in ['CreatePerson', 'UpdatePerson']:
                wrappers.add('PersonResult')
            elif operation_name in ['CreateApiKey', 'TestApiKey']:
                wrappers.add('ApiKeyResult')
            elif operation_name == 'ConvertDiagramFormat':
                wrappers.add('FormatConversionResult')
            elif operation_name in ['RegisterCliSession', 'UnregisterCliSession']:
                wrappers.add('CliSessionResult')
            elif operation_name in ['SaveFile', 'DeleteFile']:
                wrappers.add('FileOperationResult')

        result_wrappers = []
        for wrapper_name in sorted(wrappers):
            # Determine the base type from the wrapper name
            if wrapper_name == "ExecutionResult":
                base_type = "ExecutionStateType"
            elif wrapper_name == "DiagramResult":
                base_type = "DomainDiagramType"
            elif wrapper_name == "NodeResult":
                base_type = "DomainNodeType"
            elif wrapper_name == "PersonResult":
                base_type = "DomainPersonType"
            elif wrapper_name == "ApiKeyResult":
                base_type = "DomainApiKeyType"
            elif wrapper_name == "DeleteResult":
                base_type = None  # Delete results don't have a data field
            elif wrapper_name == "CliSessionResult":
                base_type = "CliSessionType"
            elif wrapper_name == "FileOperationResult":
                base_type = "FileTypeType"
            elif wrapper_name == "FormatConversionResult":
                base_type = "str"  # or appropriate type for format conversion
            else:
                base_type = "JSON"

            wrapper_def = {
                "name": wrapper_name,
                "base_type": base_type,
                "fields": [
                    {"name": "success", "type": "bool"},
                    {"name": "message", "type": "Optional[str]"}
                ]
            }

            if base_type:
                wrapper_def["fields"].append({
                    "name": "data",
                    "type": f"Optional[{base_type}]"
                })

            result_wrappers.append(wrapper_def)

        return result_wrappers

    def process_types_for_strawberry(self, interfaces: List[Dict]) -> List[Dict]:
        """Process interfaces to create Strawberry type definitions."""
        types = []

        for interface in interfaces:
            strawberry_type = {
                "name": interface["name"],
                "fields": [],
                "field_methods": interface.get("field_methods", []),
                "custom_fields": interface.get("custom_fields", []),
                "simple_fields": interface.get("simple_fields", True),
                "has_all_fields": interface.get("has_all_fields", False)
            }

            # Process regular fields
            for field in interface["fields"]:
                strawberry_field = {
                    "name": field["name"],
                    "type": field["type"],  # Raw type - template will handle conversion
                    "is_optional": field.get("is_optional", False),
                    "description": field.get("description", "")
                }
                strawberry_type["fields"].append(strawberry_field)

            types.append(strawberry_type)

        return types


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

def build_unified_ir(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Build unified IR from TypeScript AST files.
    This is the main entry point called by the diagram.

    Args:
        input_data: Input from the db node - contains AST data

    Returns:
        Complete unified IR for template rendering
    """
    # 1. Load configuration
    base_dir = Path(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))
    config_path = base_dir / "projects/codegen/config/strawberry"
    config = StrawberryConfig(config_path)

    # Create builder instance
    builder = UnifiedIRBuilder(config)

    # 2. Handle input data - the db node always wraps in 'default' key
    file_dict = input_data.get("default", {})

    # Files to exclude from domain type generation
    exclude_patterns = [
        'ast-types.ts',  # AST parsing types
        'query-specifications.ts',  # Frontend query types
        'relationship-queries.ts',  # Frontend relationship configs
        'query-types.ts',  # Query building infrastructure types (FieldArgument, etc.)
        'graphql-types.ts',  # Frontend GraphQL type definitions
        # Note: We DON'T exclude query-definitions/* because those contain actual operations
    ]

    # 3. Merge all AST files into a single structure
    merged_ast = {
        "interfaces": [],
        "enums": [],
        "brandedScalars": [],
        "inputs": [],
        "types": [],  # Add types array
        "constants": []  # Add constants array for node specs
    }

    # Each key is a file path, each value is the AST content
    for file_path, ast_content in file_dict.items():
        # Skip files that should be excluded from domain types
        if any(pattern in file_path for pattern in exclude_patterns):
            print(f"Skipping excluded file: {file_path}")
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
    print(f"Processing {len(file_dict)} AST files")
    operations = extract_operations_from_ast(file_dict)
    print(f"Extracted {len(operations)} operations")

    # Group operations by type
    queries = [op for op in operations if op['type'] == 'query']
    mutations = [op for op in operations if op['type'] == 'mutation']
    subscriptions = [op for op in operations if op['type'] == 'subscription']

    # Generate operations metadata
    operations_metadata = generate_operations_metadata(operations)

    # Collect required imports
    imports = collect_required_imports(operations)

    # 5. Build domain IR
    print(f"Merged AST has {len(merged_ast['enums'])} enums")
    print(f"Merged AST has {len(merged_ast['constants'])} constants")

    domain_ir = builder.build_domain_ir(merged_ast)
    print(f"Domain IR has {len(domain_ir['enums'])} enums after build")
    print(f"Domain IR has {len(domain_ir.get('node_specs', []))} node specs after build")

    # 6. Build operations IR
    ops_ir = builder.build_operations_ir(operations_metadata)

    # 7. Generate result wrappers
    result_wrappers = builder.generate_result_wrappers(ops_ir)

    # 8. Process types for Strawberry
    strawberry_types = builder.process_types_for_strawberry(domain_ir["interfaces"])

    # 9. Build template operations (for generated_schema.py)
    template_operations = builder.build_template_operations(operations)

    # 10. Build complete unified IR
    unified_ir = {
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
        "config": config.to_dict(),

        # Metadata
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
            "operations_meta": operations_metadata  # Include for compatibility
        }
    }

    # 10. Write unified IR to file for debugging/inspection
    ir_output_path = base_dir / "projects/codegen/ir/strawberry_ir.json"
    ir_output_path.parent.mkdir(parents=True, exist_ok=True)
    ir_output_path.write_text(json.dumps(unified_ir, indent=2))
    print(f"Wrote unified IR to {ir_output_path}")

    return unified_ir


# For backward compatibility with existing diagram nodes
def main(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Backward compatibility wrapper for existing operations extraction.
    """
    return build_unified_ir(inputs)


# Also expose the build function with the original name for compatibility
build_complete_ir = build_unified_ir
