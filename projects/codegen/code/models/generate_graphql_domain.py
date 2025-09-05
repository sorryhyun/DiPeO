"""
Extract domain types from TypeScript AST for GraphQL type generation.
"""

import ast
import json
import os
from pathlib import Path
from typing import Any


def determine_field_type(field: dict[str, Any], interface_name: str) -> dict[str, Any]:
    """Determine the GraphQL field type and characteristics from TypeScript type."""
    field_info = {
        "name": field["name"],
        "is_auto": True,  # Default to auto
        "is_enum": False,
        "is_optional": field.get("isOptional", False),
        "is_json": False,
        "type": None,
        "default": "None" if field.get("isOptional", False) else None,
    }

    type_str = field.get("type", "")

    # Check for enum types
    if "Status" in type_str:
        field_info["is_enum"] = True
        field_info["type"] = "Status"
        field_info["is_auto"] = False
    # Check for JSON/Dict types
    elif (
        "Record<" in type_str
        or "Dict" in type_str
        or field["name"]
        in [
            "data",
            "variables",
            "node_states",
            "node_outputs",
            "body",
            "metrics",
            "output",
            "exec_counts",
        ]
    ):
        field_info["is_json"] = True
        field_info["is_auto"] = False
        if field_info["is_optional"]:
            field_info["type"] = "Optional[JSONScalar]"
        else:
            field_info["type"] = "JSONScalar"
    # Check for LLM usage
    elif "LLMUsage" in type_str:
        field_info["type"] = "LLMUsageType" if field_info["is_optional"] else "LLMUsageType"
        field_info["is_auto"] = False if field_info["is_optional"] else True
    # Check for timestamp fields (can be string or number)
    elif field["name"] == "timestamp":
        field_info["is_json"] = True
        field_info["is_auto"] = False
        field_info["type"] = "Optional[JSONScalar]"

    return field_info


def extract_domain_interfaces_from_ast(ast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract domain interface definitions from TypeScript AST data."""
    domain_types = []

    # Define the interfaces we want to extract (in dependency order)
    target_interfaces = [
        "Vec2",
        "LLMUsage",
        "PersonLLMConfig",
        "NodeState",
        "EnvelopeMeta",
        "SerializedEnvelope",
        "DomainHandle",
        "DomainNode",
        "DomainArrow",
        "DomainPerson",
        "DomainApiKey",
        "DiagramMetadata",
        "ExecutionOptions",
        "ExecutionState",
        "DomainDiagram",
    ]

    # Special handling for certain types
    special_field_methods = {
        "NodeState": [
            {
                "name": "output",
                "return_type": "Optional[JSONScalar]",
                "is_optional": True,
                "description": "Node output data",
            },
        ],
        "DomainNode": [
            {
                "name": "type",
                "return_type": "str",
                "is_optional": False,
                "description": "Return the enum value (lowercase) instead of the enum name.",
            },
            {
                "name": "data",
                "return_type": "JSONScalar",
                "is_optional": False,
                "description": "Node configuration data",
            },
        ],
        "DomainArrow": [
            {
                "name": "data",
                "return_type": "Optional[JSONScalar]",
                "is_optional": True,
                "description": "Optional arrow data",
            },
        ],
        "DomainPerson": [
            {
                "name": "type",
                "return_type": "str",
                "is_optional": False,
                "description": "Always returns person",
            },
        ],
        "ExecutionOptions": [
            {
                "name": "variables",
                "return_type": "JSONScalar",
                "is_optional": False,
                "description": "Execution variables",
            },
        ],
        "ExecutionState": [
            {
                "name": "node_states",
                "return_type": "JSONScalar",
                "is_optional": False,
                "description": "Node execution states",
            },
            {
                "name": "node_outputs",
                "return_type": "JSONScalar",
                "is_optional": False,
                "description": "Node execution outputs",
            },
            {
                "name": "variables",
                "return_type": "Optional[JSONScalar]",
                "is_optional": True,
                "description": "Execution variables",
            },
            {
                "name": "exec_counts",
                "return_type": "JSONScalar",
                "is_optional": False,
                "description": "Node execution counts",
            },
            {
                "name": "metrics",
                "return_type": "Optional[JSONScalar]",
                "is_optional": True,
                "description": "Execution metrics",
            },
        ],
        "DomainDiagram": [
            {
                "name": "nodeCount",
                "return_type": "int",
                "is_optional": False,
                "description": "Returns the total number of nodes in the diagram",
            },
            {
                "name": "arrowCount",
                "return_type": "int",
                "is_optional": False,
                "description": "Returns the total number of arrows in the diagram",
            },
        ],
    }

    # Types that should use all_fields=True (no custom fields)
    simple_types = [
        "Vec2",
        "LLMUsage",
        "PersonLLMConfig",
        "DomainHandle",
        "DomainApiKey",
        "DiagramMetadata",
    ]

    # Get interfaces from the AST
    interfaces = ast_data.get("interfaces", [])

    for interface_name in target_interfaces:
        # Find the interface in the AST
        interface_data = None
        for iface in interfaces:
            if iface.get("name") == interface_name:
                interface_data = iface
                break

        if not interface_data:
            continue

        type_info = {
            "name": interface_name,
            "has_simple_fields": interface_name in simple_types,
            "has_custom_fields": interface_name not in simple_types,
            "custom_fields": [],
            "field_methods": special_field_methods.get(interface_name, []),
        }

        # Process custom fields for complex types
        if type_info["has_custom_fields"]:
            fields = interface_data.get("properties", [])

            # For certain types, we need to explicitly define fields
            if interface_name == "NodeState":
                type_info["custom_fields"] = [
                    {"name": "status", "is_auto": False, "is_enum": True, "type": "Status"},
                    {"name": "started_at", "is_auto": True},
                    {"name": "ended_at", "is_auto": True},
                    {"name": "error", "is_auto": True},
                    {"name": "llm_usage", "is_auto": True},
                ]
            elif interface_name == "EnvelopeMeta":
                type_info["custom_fields"] = [
                    {
                        "name": "node_id",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[str]",
                        "default": "None",
                    },
                    {
                        "name": "llm_usage",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[LLMUsageType]",
                        "default": "None",
                    },
                    {
                        "name": "execution_time",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[float]",
                        "default": "None",
                    },
                    {
                        "name": "retry_count",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[int]",
                        "default": "None",
                    },
                    {
                        "name": "error",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[str]",
                        "default": "None",
                    },
                    {
                        "name": "error_type",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[str]",
                        "default": "None",
                    },
                    {
                        "name": "timestamp",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[JSONScalar]",
                        "default": "None",
                    },
                ]
            elif interface_name == "SerializedEnvelope":
                type_info["custom_fields"] = [
                    {"name": "envelope_format", "is_auto": True},
                    {"name": "id", "is_auto": True},
                    {"name": "trace_id", "is_auto": True},
                    {"name": "produced_by", "is_auto": True},
                    {"name": "content_type", "is_auto": True},
                    {"name": "schema_id", "is_auto": True},
                    {"name": "serialization_format", "is_auto": True},
                    {
                        "name": "body",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[JSONScalar]",
                        "default": "None",
                    },
                    {"name": "meta", "is_auto": True},
                ]
            elif interface_name == "DomainNode":
                type_info["custom_fields"] = [
                    {"name": "id", "is_auto": True},
                    {"name": "position", "is_auto": True},
                ]
            elif interface_name == "DomainArrow":
                type_info["custom_fields"] = [
                    {"name": "id", "is_auto": True},
                    {"name": "source", "is_auto": True},
                    {"name": "target", "is_auto": True},
                    {"name": "content_type", "is_auto": True},
                    {"name": "label", "is_auto": True},
                ]
            elif interface_name == "DomainPerson":
                type_info["custom_fields"] = [
                    {"name": "id", "is_auto": True},
                    {"name": "label", "is_auto": True},
                    {"name": "llm_config", "is_auto": True},
                ]
            elif interface_name == "ExecutionOptions":
                type_info["custom_fields"] = [
                    {"name": "mode", "is_auto": True},
                    {"name": "timeout", "is_auto": True},
                ]
            elif interface_name == "ExecutionState":
                type_info["custom_fields"] = [
                    {"name": "id", "is_auto": True},
                    {"name": "status", "is_auto": False, "is_enum": True, "type": "Status"},
                    {"name": "diagram_id", "is_auto": True},
                    {"name": "started_at", "is_auto": True},
                    {"name": "ended_at", "is_auto": True},
                    {"name": "llm_usage", "is_auto": True},
                    {"name": "error", "is_auto": True},
                    {"name": "duration_seconds", "is_auto": True},
                    {"name": "is_active", "is_auto": True},
                    {"name": "executed_nodes", "is_auto": True},
                ]
            elif interface_name == "DomainDiagram":
                # DomainDiagram uses all_fields=True but has field methods
                type_info["has_simple_fields"] = False
                type_info["has_custom_fields"] = False
                # Ensure it still has the field_methods
                type_info["field_methods"] = special_field_methods.get("DomainDiagram", [])

        domain_types.append(type_info)

    return domain_types


def main(inputs: dict[str, Any]) -> dict[str, Any]:
    """
    Main entry point for GraphQL domain type extraction.

    Reads TypeScript AST files and extracts domain interfaces for generation.
    """
    import logging
    from datetime import datetime

    logger = logging.getLogger(__name__)
    logger.debug(f"Received inputs keys: {list(inputs.keys())}")

    all_domain_types = []
    scalar_types = []

    # Try multiple input formats
    ast_files = []

    # Check for 'default' key
    if "default" in inputs:
        data = inputs["default"]

        # Handle string input
        if isinstance(data, str):
            try:
                data = json.loads(data)
            except (json.JSONDecodeError, ValueError):
                try:
                    data = ast.literal_eval(data)
                except (ValueError, SyntaxError):
                    logger.debug(f"Could not parse string input: {data[:100]}")
                    data = None

        if isinstance(data, dict):
            ast_files = [data]
        elif isinstance(data, list):
            ast_files = data

    # Process AST files
    for item in ast_files:
        if isinstance(item, str):
            try:
                item = json.loads(item)
            except (json.JSONDecodeError, ValueError):
                try:
                    item = ast.literal_eval(item)
                except (ValueError, SyntaxError):
                    continue

        if isinstance(item, dict):
            # Check if it has interfaces (domain types)
            if "interfaces" in item:
                types = extract_domain_interfaces_from_ast(item)
                all_domain_types.extend(types)

            # Check if it has types (for scalars)
            if "types" in item:
                for type_def in item["types"]:
                    name = type_def.get("name", "")
                    if name.endswith("ID") and "__brand" in type_def.get("type", ""):
                        scalar_types.append(name)

    # Fallback to filesystem if needed
    if not all_domain_types:
        logger.debug("No domain types from inputs, trying filesystem fallback")
        base_dir = Path(os.getenv("DIPEO_BASE_DIR", os.getcwd()))
        temp_dir = base_dir / "temp"

        # Load diagram and execution AST files
        for file_name in ["core/diagram.ts.json", "core/execution.ts.json"]:
            ast_file = temp_dir / file_name
            if ast_file.exists():
                with open(ast_file) as f:
                    ast_data = json.load(f)
                    types = extract_domain_interfaces_from_ast(ast_data)
                    all_domain_types.extend(types)

                    # Also extract scalars
                    if "types" in ast_data:
                        for type_def in ast_data["types"]:
                            name = type_def.get("name", "")
                            if name.endswith("ID") and "__brand" in type_def.get("type", ""):
                                scalar_types.append(name)

    # Remove duplicates
    seen_types = set()
    unique_domain_types = []
    for dt in all_domain_types:
        if dt["name"] not in seen_types:
            seen_types.add(dt["name"])
            unique_domain_types.append(dt)

    # Remove duplicate scalars
    scalar_types = list(set(scalar_types))
    scalar_types.sort()

    # Create result
    result = {
        "domain_types": unique_domain_types,
        "scalar_types": scalar_types,
        "generated_at": datetime.now().isoformat(),
        "total_count": len(unique_domain_types),
    }

    return result


if __name__ == "__main__":
    # Test with mock data
    test_ast = {
        "interfaces": [
            {
                "name": "Vec2",
                "properties": [{"name": "x", "type": "number"}, {"name": "y", "type": "number"}],
            },
            {
                "name": "DomainNode",
                "properties": [
                    {"name": "id", "type": "NodeID"},
                    {"name": "type", "type": "NodeType"},
                    {"name": "position", "type": "Vec2"},
                    {"name": "data", "type": "Record<string, any>"},
                ],
            },
        ],
        "types": [
            {
                "name": "NodeID",
                "type": "string & { readonly __brand: 'NodeID' }",
                "isExported": True,
            },
        ],
    }

    result = main({"default": test_ast})
    print(json.dumps(result, indent=2))
