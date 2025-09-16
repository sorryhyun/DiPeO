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


def build_factory_data(node_specs: list[dict[str, Any]]) -> dict[str, Any]:
    """Build factory configuration from node specifications."""
    factory_data = {
        "nodes": [],
        "node_map": {},
        "categories": set(),
    }

    for spec in node_specs:
        node_entry = {
            "type": spec["node_type"],
            "name": spec["node_name"],
            "display_name": spec["display_name"],
            "category": spec["category"],
            "fields": [field["name"] for field in spec["fields"]],
        }
        factory_data["nodes"].append(node_entry)
        factory_data["node_map"][spec["node_type"]] = spec["node_name"]
        if spec["category"]:
            factory_data["categories"].add(spec["category"])

    factory_data["categories"] = sorted(list(factory_data["categories"]))
    return factory_data


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
        logger.info(f"BackendIRBuilder: Processing {len(merged_ast)} AST files")
        logger.info(f"BackendIRBuilder: Keys in source_data: {list(source_data.keys())[:5]}")

        # Create type converter
        type_converter = TypeConverter()

        # Extract all components
        node_specs = extract_node_specs(merged_ast, type_converter)
        enums = extract_enums(merged_ast)
        integrations = extract_integrations(merged_ast, type_converter)
        conversions = extract_conversions(merged_ast)
        factory_data = build_factory_data(node_specs)
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
            "integrations": integrations,
            "conversions": conversions,
            "unified_models": unified_models,
            "factory_data": factory_data,
            "typescript_indexes": typescript_indexes,
            # Metadata
            "metadata": {
                "node_count": len(node_specs),
                "enum_count": len(enums),
                "integration_model_count": len(integrations["models"]),
                "categories": factory_data["categories"],
            },
        }

        # Write IR to file for debugging/inspection
        ir_output_path = self.base_dir / "projects/codegen/ir/backend_ir.json"
        ir_output_path.parent.mkdir(parents=True, exist_ok=True)
        ir_output_path.write_text(json.dumps(ir_dict, indent=2))
        logger.info(f"Wrote backend IR to {ir_output_path}")

        # Print summary
        logger.info("Generated backend IR with:")
        logger.info(f"  - {ir_dict['metadata']['node_count']} node specifications")
        logger.info(f"  - {ir_dict['metadata']['enum_count']} enums")
        logger.info(f"  - {ir_dict['metadata']['integration_model_count']} integration models")
        logger.info(f"  - {len(ir_dict['metadata']['categories'])} categories")

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
