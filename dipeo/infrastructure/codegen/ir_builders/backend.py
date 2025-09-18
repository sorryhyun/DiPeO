"""Backend IR builder implementation."""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

from dipeo.domain.codegen.ir_builder_port import IRData
from dipeo.infrastructure.codegen.ir_builders.base import BaseIRBuilder
from dipeo.infrastructure.codegen.ir_builders.utils import (
    TypeConverter,
    camel_to_snake,
    extract_constants_from_ast,
    extract_enums_from_ast,
    extract_interfaces_from_ast,
    get_default_value,
    process_field_definition,
    snake_to_pascal,
)

logger = logging.getLogger(__name__)


# ============================================================================
# NODE SPECS EXTRACTION
# ============================================================================


def extract_node_specs(
    ast_data: dict[str, Any], type_converter: Optional[TypeConverter] = None
) -> list[dict[str, Any]]:
    """Extract node specifications from TypeScript AST."""
    if not type_converter:
        type_converter = TypeConverter()

    node_specs = []

    for file_path, file_data in ast_data.items():
        if not file_path.endswith(".spec.ts.json"):
            continue

        # Extract node type from filename
        base_name = Path(file_path).stem.replace(".spec.ts", "")
        node_type = base_name.replace("-", "_")
        node_name = snake_to_pascal(node_type)

        # Look for the specification constant
        for const in file_data.get("constants", []):
            const_name = const.get("name", "")
            # Check for spec constants (could be 'apiJobSpec' or 'apiJobSpecification')
            if const_name.endswith("Spec") or const_name.endswith("Specification"):
                spec_value = const.get("value", {})
                if not isinstance(spec_value, dict):
                    continue

                fields = []
                for field in spec_value.get("fields", []):
                    field_def = {
                        "name": field.get("name", ""),
                        "type": type_converter.ts_to_python(field.get("type", "any")),
                        "required": field.get("required", False),
                        "default": field.get("defaultValue"),
                        "description": field.get("description", ""),
                        "validation": field.get("validation", {}),
                    }
                    fields.append(field_def)

                node_spec = {
                    "node_type": node_type,
                    "node_name": node_name,
                    "display_name": spec_value.get("displayName", node_name),
                    "category": spec_value.get("category", ""),
                    "description": spec_value.get("description", ""),
                    "fields": fields,
                    "icon": spec_value.get("icon", ""),
                    "color": spec_value.get("color", ""),
                }
                node_specs.append(node_spec)
                break

    return node_specs


# ============================================================================
# ENUMS EXTRACTION
# ============================================================================


def extract_enums(ast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract enum definitions from TypeScript AST."""
    enums = []
    processed_enums = set()

    for _file_path, file_data in ast_data.items():
        for enum in file_data.get("enums", []):
            enum_name = enum.get("name", "")

            # Skip if already processed or is frontend-only
            if enum_name in processed_enums:
                continue
            if enum_name in {
                "QueryOperationType",
                "CrudOperation",
                "QueryEntity",
                "FieldPreset",
                "FieldGroup",
            }:
                continue

            processed_enums.add(enum_name)

            # Extract enum values
            values = []
            if "members" in enum:
                for member in enum["members"]:
                    values.append(
                        {
                            "name": member.get("name", ""),
                            "value": member.get("value", member.get("name", "").lower()),
                        }
                    )
            elif "values" in enum:
                for value in enum["values"]:
                    if isinstance(value, str):
                        values.append({"name": value, "value": value.lower()})
                    elif isinstance(value, dict):
                        values.append(value)

            enum_def = {
                "name": enum_name,
                "values": values,
                "description": enum.get("description", ""),
            }
            enums.append(enum_def)

    return enums


# ============================================================================
# DOMAIN MODELS EXTRACTION
# ============================================================================


def extract_domain_models(
    ast_data: dict[str, Any], type_converter: Optional[TypeConverter] = None
) -> dict[str, Any]:
    """Extract domain model definitions from TypeScript AST."""
    if not type_converter:
        type_converter = TypeConverter()

    domain_models = {"newtypes": [], "models": [], "aliases": []}

    processed_newtypes = set()
    processed_models = set()

    # Define which files contain domain models
    domain_files = [
        "core/diagram.ts",
        "core/execution.ts",
        "core/conversation.ts",
        "core/cli-session.ts",
        "core/file.ts",
    ]

    for file_path, file_data in ast_data.items():
        # Check if this is a domain model file
        is_domain_file = any(file_path.endswith(f"{df}.json") for df in domain_files)
        if not is_domain_file:
            continue

        # Extract NewType declarations (branded types)
        for type_alias in file_data.get("types", []):
            type_name = type_alias.get("name", "")
            type_text = type_alias.get("type", "")

            # Check if it's a branded type (NewType pattern)
            if "readonly __brand:" in type_text and type_name not in processed_newtypes:
                # Extract base type from "string & { readonly __brand: 'NodeID' }"
                base_type = type_text.split(" & ")[0].strip()
                python_base = type_converter.ts_to_python(base_type)
                domain_models["newtypes"].append({"name": type_name, "base": python_base})
                processed_newtypes.add(type_name)

        # Extract interfaces as models
        for interface in file_data.get("interfaces", []):
            interface_name = interface.get("name", "")

            # Skip if already processed or is a utility interface
            if interface_name in processed_models:
                continue
            if interface_name in {"BaseNodeData", "NodeSpecification"}:
                continue

            processed_models.add(interface_name)

            # Extract fields
            fields = []
            for prop in interface.get("properties", []):
                field_name = prop.get("name", "")
                field_type = prop.get("type", {})
                is_optional = prop.get("optional", False)

                # Convert TypeScript type to Python type
                if isinstance(field_type, dict):
                    type_text = field_type.get("text", "any")
                else:
                    type_text = str(field_type)

                python_type = type_converter.ts_to_python(type_text)

                # Handle literal types
                is_literal = False
                literal_value = None
                if isinstance(field_type, dict) and field_type.get("kind") == "literal":
                    is_literal = True
                    literal_value = field_type.get("value")
                    if literal_value == "true":
                        literal_value = True
                        python_type = "Literal[True]"
                    elif isinstance(literal_value, str):
                        python_type = f'Literal["{literal_value}"]'

                fields.append(
                    {
                        "name": camel_to_snake(field_name)
                        if field_name not in {"id", "type"}
                        else field_name,
                        "python_type": python_type,
                        "optional": is_optional,
                        "literal": is_literal,
                        "literal_value": literal_value,
                        "description": prop.get("description", ""),
                    }
                )

            # Add the model
            description = interface.get("description", "")
            if not description:
                description = f"{interface_name} model"

            domain_models["models"].append(
                {"name": interface_name, "fields": fields, "description": description}
            )

    # Add type aliases
    domain_models["aliases"].extend(
        [
            {"name": "SerializedNodeOutput", "type": "SerializedEnvelope"},
            {"name": "PersonMemoryMessage", "type": "Message"},
        ]
    )

    return domain_models


# ============================================================================
# NODE FACTORY DATA EXTRACTION
# ============================================================================


def build_node_factory_data(node_specs: list[dict[str, Any]]) -> dict[str, Any]:
    """Build factory data for node creation from specs."""
    factory_data = {"imports": [], "factory_cases": [], "categories": []}

    seen_categories = set()

    for spec in node_specs:
        node_type = spec["node_type"]
        node_name = spec["node_name"]
        category = spec.get("category", "")

        # Build import statement
        # Convert node_name from PascalCase to snake_case and add _node suffix
        module_name = f"unified_nodes.{camel_to_snake(node_name)}_node"
        factory_data["imports"].append(
            {
                "module": module_name,
                "class": f"{node_name}Node",
                "alias": "DBNode" if node_type == "db" else None,
            }
        )

        # Build factory case
        field_mappings = []
        for field in spec["fields"]:
            field_name = field["name"]
            # Handle special field name mappings
            if field_name == "file_path":
                getter = "data.get('filePath', data.get('file_path', ''))"
            elif field_name == "function_name":
                getter = "data.get('functionName', data.get('function_name', ''))"
            elif field_name == "condition_type":
                getter = "data.get('condition_type')"
            elif field_name == "expression":
                getter = "data.get('expression', data.get('condition', ''))"
            else:
                default_val = field.get("default")
                if default_val is not None:
                    if isinstance(default_val, str):
                        getter = f"data.get('{field_name}', '{default_val}')"
                    else:
                        getter = f"data.get('{field_name}', {default_val})"
                else:
                    getter = f"data.get('{field_name}')"

            field_mappings.append({"node_field": field_name, "getter_expression": getter})

        factory_data["factory_cases"].append(
            {
                "node_type": f"NodeType.{node_type.upper()}",
                "class_name": f"{node_name}Node",
                "field_mappings": field_mappings,
            }
        )

        # Track categories
        if category and category not in seen_categories:
            seen_categories.add(category)
            factory_data["categories"].append(category)

    return factory_data


# ============================================================================
# INTEGRATIONS EXTRACTION
# ============================================================================


def extract_integrations(
    ast_data: dict[str, Any], type_converter: Optional[TypeConverter] = None
) -> dict[str, Any]:
    """Extract integration configurations from TypeScript AST."""
    if not type_converter:
        type_converter = TypeConverter()

    integrations = {
        "models": [],
        "functions": [],
        "configs": [],
    }

    for file_path, file_data in ast_data.items():
        # Check for integration files more broadly
        if "integration" not in file_path.lower() and not file_path.endswith("integration.ts.json"):
            continue

        # Extract all interfaces from integration files
        for interface in file_data.get("interfaces", []):
            # Include all interfaces from integration files, not just those with 'Integration' in name
            model = {
                "name": interface["name"],
                "fields": [],
            }
            for prop in interface.get("properties", []):
                field = {
                    "name": prop["name"],
                    "type": type_converter.ts_to_python(prop.get("type", "any")),
                    "optional": prop.get("optional", prop.get("isOptional", False)),
                }
                model["fields"].append(field)
            integrations["models"].append(model)

        # Extract integration configs from constants
        for const in file_data.get("constants", []):
            if "config" in const.get("name", "").lower():
                config = {
                    "name": const["name"],
                    "value": const.get("value", {}),
                }
                integrations["configs"].append(config)

    return integrations


# ============================================================================
# CONVERSIONS EXTRACTION
# ============================================================================


def extract_conversions(ast_data: dict[str, Any]) -> dict[str, Any]:
    """Extract type conversion mappings from TypeScript AST."""
    conversions = {
        "node_type_map": {},
        "type_conversions": {},
        "field_mappings": {},
    }

    for file_path, file_data in ast_data.items():
        # Check for conversion/mapping files more broadly
        if (
            "conversion" not in file_path.lower()
            and "mapping" not in file_path.lower()
            and not file_path.endswith("conversions.ts.json")
            and not file_path.endswith("mappings.ts.json")
        ):
            continue

        # Extract all constants from conversion/mapping files
        for const in file_data.get("constants", []):
            const_name = const.get("name", "")
            const_value = const.get("value", {})

            # Handle NODE_TYPE_MAP
            if "NODE_TYPE_MAP" in const_name:
                # Parse the JavaScript object literal string if needed
                if isinstance(const_value, str) and "{" in const_value:
                    # This is a JavaScript literal, extract key-value pairs
                    import re

                    matches = re.findall(r"'([^']+)':\s*NodeType\.([A-Z_]+)", const_value)
                    for key, value in matches:
                        conversions["node_type_map"][key] = value
                elif isinstance(const_value, dict):
                    for key, value in const_value.items():
                        if isinstance(value, dict):
                            conversions["node_type_map"][key] = value.get("value", key)
                        else:
                            conversions["node_type_map"][key] = str(value)

            # Handle TS_TO_PY_TYPE
            elif "TS_TO_PY" in const_name and isinstance(const_value, dict):
                # Clean up the keys (remove quotes)
                for key, value in const_value.items():
                    clean_key = key.strip("'\"")
                    conversions["type_conversions"][clean_key] = value

            # Handle TYPE_TO_FIELD
            elif "TYPE_TO_FIELD" in const_name and isinstance(const_value, dict):
                for key, value in const_value.items():
                    clean_key = key.strip("'\"")
                    conversions["field_mappings"][clean_key] = value

            # Handle other conversion/mapping constants
            elif "Conversion" in const_name and isinstance(const_value, dict):
                conversions["type_conversions"].update(const_value)
            elif "Mapping" in const_name and isinstance(const_value, dict):
                conversions["field_mappings"].update(const_value)

    return conversions


# ============================================================================
# FACTORY DATA EXTRACTION
# ============================================================================


# ============================================================================
# TYPESCRIPT INDEXES EXTRACTION
# ============================================================================


def extract_typescript_indexes(base_dir: Path) -> dict[str, Any]:
    """Generate TypeScript index exports configuration."""
    indexes = {
        "node_specs": [],
        "types": [],
        "utils": [],
    }

    # Scan for TypeScript files that should be indexed
    specs_dir = base_dir / "dipeo/models/src/node-specs"
    if specs_dir.exists():
        for spec_file in specs_dir.glob("*.spec.ts"):
            spec_name = spec_file.stem.replace(".spec", "")
            registry_key = camel_to_snake(spec_name)
            indexes["node_specs"].append(
                {
                    "file": spec_file.name,
                    "name": spec_name,
                    "registry_key": registry_key,
                }
            )

    return indexes


# ============================================================================
# BACKEND IR BUILDER CLASS
# ============================================================================


class BackendIRBuilder(BaseIRBuilder):
    """Build IR for backend code generation."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize backend IR builder.

        Args:
            config_path: Optional path to configuration file
        """
        super().__init__(config_path or "projects/codegen/config/backend")
        self.base_dir = Path(os.environ.get("DIPEO_BASE_DIR", "/home/soryhyun/DiPeO"))

    async def build_ir(
        self, source_data: dict[str, Any], config: Optional[dict[str, Any]] = None
    ) -> IRData:
        """Build IR from source data.

        Args:
            source_data: Input AST data to build IR from
            config: Optional configuration parameters

        Returns:
            IRData containing the built backend IR
        """
        # Handle input data - the db node always wraps in 'default' key
        if "default" in source_data:
            file_dict = source_data.get("default", {})
        else:
            file_dict = source_data

        # Merge all AST files
        merged_ast = {}
        for file_path, ast_content in file_dict.items():
            if isinstance(ast_content, dict):
                merged_ast[file_path] = ast_content

        # Debug logging
        # logger.info(f"BackendIRBuilder: Processing {len(merged_ast)} AST files")
        # logger.info(f"BackendIRBuilder: Keys in source_data: {list(source_data.keys())[:5]}")

        # Create type converter
        type_converter = TypeConverter()

        # Extract all components
        node_specs = extract_node_specs(merged_ast, type_converter)
        enums = extract_enums(merged_ast)
        domain_models = extract_domain_models(merged_ast, type_converter)
        integrations = extract_integrations(merged_ast, type_converter)
        conversions = extract_conversions(merged_ast)
        node_factory = build_node_factory_data(node_specs)
        typescript_indexes = extract_typescript_indexes(self.base_dir)

        # Build unified models data
        unified_models = []
        for spec in node_specs:
            model = {
                "class_name": spec["node_name"],
                "display_name": spec["display_name"],
                "description": spec["description"],
                "fields": spec["fields"],
                "category": spec["category"],
                "icon": spec["icon"],
                "color": spec["color"],
            }
            unified_models.append(model)

        # Build complete IR
        ir_dict = {
            "version": 1,
            "generated_at": datetime.now().isoformat(),
            # Core data
            "node_specs": node_specs,
            "enums": enums,
            "domain_models": domain_models,
            "integrations": integrations,
            "conversions": conversions,
            "unified_models": unified_models,
            "node_factory": node_factory,
            "typescript_indexes": typescript_indexes,
            # Metadata
            "metadata": {
                "node_count": len(node_specs),
                "enum_count": len(enums),
                "domain_model_count": len(domain_models["models"]),
                "integration_model_count": len(integrations["models"]),
                "categories": node_factory["categories"],
            },
        }

        # Write IR to file for debugging/inspection
        ir_output_path = self.base_dir / "projects/codegen/ir/backend_ir.json"
        ir_output_path.parent.mkdir(parents=True, exist_ok=True)
        ir_output_path.write_text(json.dumps(ir_dict, indent=2))
        logger.info(f"Wrote backend IR to {ir_output_path}")

        # Create metadata
        metadata = self.create_metadata(source_data, "backend")

        # Return wrapped IR data
        return IRData(metadata=metadata, data=ir_dict)

    def validate_ir(self, ir_data: IRData) -> bool:
        """Validate backend IR structure.

        Args:
            ir_data: IR data to validate

        Returns:
            True if valid, False otherwise
        """
        if not super().validate_ir(ir_data):
            return False

        # Check for required backend fields
        data = ir_data.data
        required_keys = ["node_specs", "enums", "metadata"]

        for key in required_keys:
            if key not in data:
                return False

        # Validate metadata
        if "node_count" not in data.get("metadata", {}):
            return False

        return True
