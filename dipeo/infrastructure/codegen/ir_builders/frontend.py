"""Frontend IR builder implementation."""

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
    extract_constants_from_ast,
    extract_interfaces_from_ast,
    pascal_to_camel,
    snake_to_pascal,
)

logger = logging.getLogger(__name__)


# ============================================================================
# NODE CONFIGS EXTRACTION
# ============================================================================


def extract_node_configs(ast_data: dict[str, Any]) -> list[dict[str, Any]]:
    """Extract frontend node configurations from TypeScript AST."""
    node_configs = []

    for file_path, file_data in ast_data.items():
        if not file_path.endswith(".spec.ts.json"):
            continue

        # Extract node type from filename
        base_name = Path(file_path).stem.replace(".spec.ts", "")
        node_type = base_name.replace("-", "_")
        node_name = snake_to_pascal(node_type)
        config_name = f"{node_name}Config"

        # Look for the specification constant
        for const in file_data.get("constants", []):
            const_name = const.get("name", "")
            # Check for spec constants (could be 'apiJobSpec' or 'apiJobSpecification')
            if const_name.endswith("Spec") or const_name.endswith("Specification"):
                spec_value = const.get("value", {})
                if not isinstance(spec_value, dict):
                    continue

                # Extract UI-specific configuration
                ui_config = {
                    "name": config_name,
                    "node_type": node_type,
                    "node_name": node_name,
                    "display_name": spec_value.get("displayName", node_name),
                    "category": spec_value.get("category", ""),
                    "description": spec_value.get("description", ""),
                    "icon": spec_value.get("icon", ""),
                    "color": spec_value.get("color", "#666"),
                    "fields": [],
                    "validation_schema": None,
                }

                # Process fields - pass raw data, let templates handle type mapping
                for field in spec_value.get("fields", []):
                    # Handle enum fields properly - if a field has an enum property,
                    # its type should be 'string' not 'enum'
                    field_type = field.get("type", "string")
                    if field_type == "enum" or field.get("enum"):
                        field_type = "string"  # Enum fields are string unions in TypeScript

                    field_config = {
                        "name": field.get("name", ""),
                        "type": field_type,  # Use corrected type
                        "label": field.get("label", field.get("name", "")),
                        "placeholder": field.get("placeholder", ""),
                        "help_text": field.get("description", ""),
                        "required": field.get("required", False),
                        "default_value": field.get("defaultValue"),
                        "validation": field.get("validation", {}),
                        "options": field.get("options", []),
                        "enum": field.get("enum", []),  # Preserve enum values for template use
                    }
                    ui_config["fields"].append(field_config)

                node_configs.append(ui_config)
                break

    return node_configs


# ============================================================================
# FIELD CONFIGS EXTRACTION
# ============================================================================


def generate_field_configs(node_configs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate field configuration objects from node configs."""
    # This is simplified now - templates handle field type mapping
    # Just return empty list as field configs are handled in templates
    return []


# ============================================================================
# GRAPHQL QUERIES EXTRACTION
# ============================================================================


def extract_graphql_queries(
    ast_data: dict[str, Any], type_converter: Optional[TypeConverter] = None
) -> list[dict[str, Any]]:
    """Extract GraphQL query definitions from TypeScript AST."""
    if not type_converter:
        type_converter = TypeConverter()

    queries = []

    for file_path, file_data in ast_data.items():
        if "query-definitions" not in file_path:
            continue

        # Extract queries from constants
        for const in file_data.get("constants", []):
            const_value = const.get("value", {})
            if isinstance(const_value, dict) and "queries" in const_value:
                entity = const_value.get("entity", "Unknown")

                for query in const_value.get("queries", []):
                    query_def = {
                        "name": query.get("name", ""),
                        "entity": entity,
                        "type": extract_operation_type(query),
                        "variables": transform_variables(
                            query.get("variables", []), type_converter
                        ),
                        "fields": transform_fields(query.get("fields", [])),
                    }
                    queries.append(query_def)

    return queries


def extract_operation_type(query_def: dict[str, Any]) -> str:
    """Extract operation type from query definition."""
    type_value = query_def.get("type", "query")
    if "." in type_value:
        return type_value.split(".")[-1].lower()
    return type_value.lower()


def transform_variables(
    variables: list[dict[str, Any]], type_converter: Optional[TypeConverter] = None
) -> list[dict[str, Any]]:
    """Transform GraphQL variables to frontend format."""
    if not type_converter:
        type_converter = TypeConverter()

    transformed = []
    for var in variables:
        transformed.append(
            {
                "name": var.get("name", ""),
                "type": type_converter.graphql_to_ts(var.get("type", "String")),
                "graphql_type": var.get("type", "String"),
                "required": var.get("required", False),
            }
        )
    return transformed


def transform_fields(fields: Any) -> list[dict[str, Any]]:
    """Transform GraphQL fields to frontend format."""
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
                    "args": field.get("args", []),
                    "fields": transform_fields(field.get("fields", [])),
                }
                transformed.append(field_def)
        return transformed

    return []


# ============================================================================
# REGISTRY DATA GENERATION
# ============================================================================


def build_registry_data(node_configs: list[dict[str, Any]]) -> dict[str, Any]:
    """Build node registry configuration."""
    registry = {
        "nodes": {},
        "categories": {},
        "icons": {},
    }

    for config in node_configs:
        node_type = config["node_type"]
        category = config["category"]

        # Add to nodes registry
        registry["nodes"][node_type] = {
            "component": f'{config["node_name"]}Node',
            "config": config["name"],
            "category": category,
        }

        # Add to categories
        if category:
            if category not in registry["categories"]:
                registry["categories"][category] = []
            registry["categories"][category].append(node_type)

        # Add icon mapping
        if config["icon"]:
            registry["icons"][node_type] = config["icon"]

    return registry


# ============================================================================
# TYPESCRIPT MODELS GENERATION
# ============================================================================


def generate_typescript_models(node_configs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Generate TypeScript model definitions from node configs."""
    models = []

    for config in node_configs:
        model = {
            "name": f'{config["node_name"]}Model',
            "interface_name": f'I{config["node_name"]}',
            "fields": [],
        }

        for field in config["fields"]:
            ts_field = {
                "name": field["name"],
                "type": field["type"],
                "optional": not field["required"],
                "description": field.get("help_text", ""),
            }
            model["fields"].append(ts_field)

        models.append(model)

    return models


# ============================================================================
# FRONTEND IR BUILDER CLASS
# ============================================================================


class FrontendIRBuilder(BaseIRBuilder):
    """Build IR for frontend code generation."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize frontend IR builder.

        Args:
            config_path: Optional path to configuration file
        """
        super().__init__(config_path or "projects/codegen/config/frontend")
        self.base_dir = Path(os.environ.get("DIPEO_BASE_DIR", "/home/soryhyun/DiPeO"))

    async def build_ir(
        self, source_data: dict[str, Any], config: Optional[dict[str, Any]] = None
    ) -> IRData:
        """Build IR from source data.

        Args:
            source_data: Input AST data to build IR from
            config: Optional configuration parameters

        Returns:
            IRData containing the built frontend IR
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
        logger.info(f"FrontendIRBuilder: Processing {len(merged_ast)} AST files")

        # Create type converter
        type_converter = TypeConverter()

        # Extract all components
        node_configs = extract_node_configs(merged_ast)
        field_configs = generate_field_configs(node_configs)
        graphql_queries = extract_graphql_queries(merged_ast, type_converter)
        registry_data = build_registry_data(node_configs)
        typescript_models = generate_typescript_models(node_configs)

        # Build complete IR
        ir_dict = {
            "version": 1,
            "generated_at": datetime.now().isoformat(),
            # Core data
            "node_configs": node_configs,
            "field_configs": field_configs,
            "graphql_queries": graphql_queries,
            "registry_data": registry_data,
            "typescript_models": typescript_models,
            # Organized by operation type for templates
            "queries": [q for q in graphql_queries if q["type"] == "query"],
            "mutations": [q for q in graphql_queries if q["type"] == "mutation"],
            "subscriptions": [q for q in graphql_queries if q["type"] == "subscription"],
            # Metadata
            "metadata": {
                "node_count": len(node_configs),
                "field_type_count": len(field_configs),
                "query_count": len([q for q in graphql_queries if q["type"] == "query"]),
                "mutation_count": len([q for q in graphql_queries if q["type"] == "mutation"]),
                "subscription_count": len(
                    [q for q in graphql_queries if q["type"] == "subscription"]
                ),
                "categories": list(registry_data["categories"].keys()),
            },
        }

        # Write IR to file for debugging/inspection
        ir_output_path = self.base_dir / "projects/codegen/ir/frontend_ir.json"
        ir_output_path.parent.mkdir(parents=True, exist_ok=True)
        ir_output_path.write_text(json.dumps(ir_dict, indent=2))
        logger.info(f"Wrote frontend IR to {ir_output_path}")

        # Create metadata
        metadata = self.create_metadata(source_data, "frontend")

        # Return wrapped IR data
        return IRData(metadata=metadata, data=ir_dict)

    def validate_ir(self, ir_data: IRData) -> bool:
        """Validate frontend IR structure.

        Args:
            ir_data: IR data to validate

        Returns:
            True if valid, False otherwise
        """
        if not super().validate_ir(ir_data):
            return False

        # Check for required frontend fields
        # Updated to match actual IR structure from frontend_ir_builder.py
        data = ir_data.data
        required_keys = ["node_configs", "field_configs", "metadata"]
        # Also accept alternative keys for backward compatibility
        alternative_keys = {"node_configs": "components", "field_configs": "schemas"}

        for key in required_keys:
            if key not in data:
                # Check if alternative key exists
                alt_key = alternative_keys.get(key)
                if (alt_key and alt_key not in data) or not alt_key:
                    return False

        # Validate metadata - check for actual metadata fields
        metadata = data.get("metadata", {})
        if not metadata:
            return False

        # Check for at least one of these metadata fields
        metadata_fields = ["node_count", "component_count", "ast_file_count", "field_config_count"]
        has_metadata = any(field in metadata for field in metadata_fields)
        if not has_metadata:
            return False

        return True
