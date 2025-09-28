"""UI configuration generation module for frontend."""

from __future__ import annotations

from typing import Any

from dipeo.infrastructure.codegen.ir_builders.core import (
    BuildContext,
    BuildStep,
    StepResult,
    StepType,
)
from dipeo.infrastructure.codegen.ir_builders.utils import snake_to_pascal


class ExtractNodeConfigsStep(BuildStep):
    """Step to extract node configurations for UI."""

    def __init__(self):
        """Initialize node configs extraction step."""
        super().__init__(name="extract_node_configs", step_type=StepType.EXTRACT, required=True)

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Extract node configurations from AST data.

        Args:
            context: Build context with utilities
            input_data: TypeScript AST data or processed node specs

        Returns:
            StepResult with node configurations
        """
        # Check if we're receiving raw AST or processed node specs
        if isinstance(input_data, dict):
            if "extract_node_specs" in input_data:
                # Coming from dependency
                node_specs = input_data["extract_node_specs"]
            else:
                # Raw AST data - extract node specs first
                from dipeo.infrastructure.codegen.ir_builders.modules.node_specs import (
                    ExtractNodeSpecsStep,
                )

                spec_step = ExtractNodeSpecsStep()
                spec_result = spec_step.execute(context, input_data)
                if not spec_result.success:
                    return spec_result
                node_specs = spec_result.data
        elif isinstance(input_data, list):
            # Already processed node specs
            node_specs = input_data
        else:
            return StepResult(
                success=False, error="Expected AST data or node specifications as input"
            )

        node_configs = self._build_node_configs(node_specs)

        return StepResult(
            success=True, data=node_configs, metadata={"config_count": len(node_configs)}
        )

    def _build_node_configs(self, node_specs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Build node configurations from specifications.

        Args:
            node_specs: List of node specifications

        Returns:
            List of node configurations
        """
        configs = []
        for spec in node_specs:
            config = {
                "node_type": spec.get("node_type", ""),
                "node_name": spec.get("node_name", ""),
                "name": spec.get("name", ""),
                "display_name": spec.get("display_name", ""),
                "category": spec.get("category", ""),
                "description": spec.get("description", ""),
                "icon": spec.get("icon", ""),
                "color": spec.get("color", ""),
                "fields": self._process_ui_fields(spec.get("fields", [])),
                "handles": spec.get("spec", {}).get("handles", {}),
                "outputs": spec.get("spec", {}).get("outputs", {}),
                "primaryDisplayField": spec.get("spec", {}).get("primaryDisplayField", ""),
            }
            configs.append(config)
        return configs

    def _process_ui_fields(self, fields: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Process fields for UI configuration.

        Args:
            fields: Field definitions from node spec

        Returns:
            Processed field definitions for UI
        """
        ui_fields = []
        for field in fields:
            ui_field = {
                "name": field.get("name", ""),
                "type": field.get("type", "string"),
                "label": field.get("name", "").replace("_", " ").title(),
                "required": field.get("required", False),
                "description": field.get("description", ""),
                "help_text": field.get("description", ""),
                "default": field.get("default"),
                "validation": field.get("validation", {}),
                "uiConfig": field.get("uiConfig", {}),
                "is_enum": field.get("is_enum", False),
                "enum_values": field.get("enum_values", []),
            }
            ui_fields.append(ui_field)
        return ui_fields


class BuildNodeRegistryStep(BuildStep):
    """Step to build node registry for frontend."""

    def __init__(self):
        """Initialize registry builder step."""
        super().__init__(name="build_node_registry", step_type=StepType.TRANSFORM, required=True)
        self.add_dependency("extract_node_configs")

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Build node registry from configurations.

        Args:
            context: Build context
            input_data: Dictionary with node configs from extraction step

        Returns:
            StepResult with registry data
        """
        # Handle input from dependencies
        if isinstance(input_data, dict) and "extract_node_configs" in input_data:
            node_configs = input_data["extract_node_configs"]
        elif isinstance(input_data, list):
            node_configs = input_data
        else:
            return StepResult(success=False, error="Expected node configurations as input")

        registry = self._build_registry(node_configs)

        return StepResult(
            success=True,
            data=registry,
            metadata={
                "node_count": len(registry["nodes"]),
                "category_count": len(registry["categories"]),
            },
        )

    def _build_registry(self, node_configs: list[dict[str, Any]]) -> dict[str, Any]:
        """Build node registry configuration.

        Args:
            node_configs: List of node configurations

        Returns:
            Registry data dictionary
        """
        registry = {
            "nodes": {},
            "categories": {},
            "icons": {},
            "colors": {},
            "display_names": {},
        }

        for config in node_configs:
            node_type = config["node_type"]
            category = config["category"]

            # Add to nodes registry
            registry["nodes"][node_type] = {
                "component": f'{config["node_name"]}Node',
                "config": config["name"],
                "category": category,
                "display_name": config["display_name"],
            }

            # Add to categories
            if category:
                if category not in registry["categories"]:
                    registry["categories"][category] = []
                registry["categories"][category].append(node_type)

            # Add icon mapping
            if config["icon"]:
                registry["icons"][node_type] = config["icon"]

            # Add color mapping
            if config["color"]:
                registry["colors"][node_type] = config["color"]

            # Add display name mapping
            registry["display_names"][node_type] = config["display_name"]

        return registry


class GenerateFieldConfigsStep(BuildStep):
    """Step to generate field configurations for UI components."""

    def __init__(self):
        """Initialize field configs generator step."""
        super().__init__(
            name="generate_field_configs", step_type=StepType.TRANSFORM, required=False
        )
        self.add_dependency("extract_node_configs")

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Generate field configurations.

        Args:
            context: Build context
            input_data: Dictionary with node configs from extraction step

        Returns:
            StepResult with field configurations
        """
        # Handle input from dependencies
        if isinstance(input_data, dict) and "extract_node_configs" in input_data:
            node_configs = input_data["extract_node_configs"]
        elif isinstance(input_data, list):
            node_configs = input_data
        else:
            return StepResult(success=False, error="Expected node configurations as input")

        field_configs = self._generate_field_configs(node_configs)

        return StepResult(
            success=True, data=field_configs, metadata={"field_config_count": len(field_configs)}
        )

    def _generate_field_configs(self, node_configs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Generate field configuration objects.

        Args:
            node_configs: List of node configurations

        Returns:
            List of field configurations
        """
        # Collect unique field types and configurations
        field_configs = {}

        for config in node_configs:
            for field in config.get("fields", []):
                field_type = field.get("type", "string")
                field_key = f"{field_type}_{field.get('is_enum', False)}"

                if field_key not in field_configs:
                    field_configs[field_key] = {
                        "type": field_type,
                        "component": self._get_field_component(field),
                        "is_enum": field.get("is_enum", False),
                        "validation_rules": self._extract_validation_rules(field),
                    }

        return list(field_configs.values())

    def _get_field_component(self, field: dict[str, Any]) -> str:
        """Determine UI component for field.

        Args:
            field: Field definition

        Returns:
            Component name
        """
        field_type = field.get("type", "string").lower()
        is_enum = field.get("is_enum", False)
        ui_config = field.get("uiConfig", {})

        # Check UI config for explicit component
        if "component" in ui_config:
            return ui_config["component"]

        # Determine by type and characteristics
        if is_enum:
            return "SelectField"
        elif field_type == "boolean":
            return "CheckboxField"
        elif field_type == "number":
            return "NumberField"
        elif field_type in {"object", "dict"}:
            return "JsonField"
        elif field_type in {"array", "list"}:
            return "ArrayField"
        elif "multiline" in ui_config or field_type == "text":
            return "TextareaField"
        else:
            return "TextField"

    def _extract_validation_rules(self, field: dict[str, Any]) -> dict[str, Any]:
        """Extract validation rules for field.

        Args:
            field: Field definition

        Returns:
            Validation rules dictionary
        """
        validation = field.get("validation", {})
        rules = {}

        if field.get("required"):
            rules["required"] = True

        if "min" in validation:
            rules["min"] = validation["min"]
        if "max" in validation:
            rules["max"] = validation["max"]
        if "pattern" in validation:
            rules["pattern"] = validation["pattern"]
        if "allowedValues" in validation:
            rules["enum"] = validation["allowedValues"]

        return rules


class GenerateTypeScriptModelsStep(BuildStep):
    """Step to generate TypeScript model definitions."""

    def __init__(self):
        """Initialize TypeScript models generator step."""
        super().__init__(
            name="generate_typescript_models", step_type=StepType.TRANSFORM, required=False
        )
        self.add_dependency("extract_node_configs")

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Generate TypeScript model definitions.

        Args:
            context: Build context
            input_data: Dictionary with node configs from extraction step

        Returns:
            StepResult with TypeScript models
        """
        # Handle input from dependencies
        if isinstance(input_data, dict) and "extract_node_configs" in input_data:
            node_configs = input_data["extract_node_configs"]
        elif isinstance(input_data, list):
            node_configs = input_data
        else:
            return StepResult(success=False, error="Expected node configurations as input")

        models = self._generate_typescript_models(node_configs)

        return StepResult(success=True, data=models, metadata={"model_count": len(models)})

    def _generate_typescript_models(
        self, node_configs: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Generate TypeScript model definitions.

        Args:
            node_configs: List of node configurations

        Returns:
            List of TypeScript model definitions
        """
        models = []

        for config in node_configs:
            model = {
                "name": f'{config["node_name"]}Model',
                "interface_name": f'I{config["node_name"]}',
                "node_type": config["node_type"],
                "fields": [],
            }

            for field in config["fields"]:
                ts_field = {
                    "name": field["name"],
                    "type": self._map_to_typescript_type(field),
                    "optional": not field["required"],
                    "description": field.get("description", ""),
                    "default": field.get("default"),
                }
                model["fields"].append(ts_field)

            models.append(model)

        return models

    def _map_to_typescript_type(self, field: dict[str, Any]) -> str:
        """Map field type to TypeScript type.

        Args:
            field: Field definition

        Returns:
            TypeScript type string
        """
        field_type = field.get("type", "string").lower()
        is_enum = field.get("is_enum", False)

        if is_enum and field.get("enum_values"):
            # Create union type from enum values
            values = field["enum_values"]
            if all(isinstance(v, str) for v in values):
                return " | ".join(f'"{v}"' for v in values)
            return "string"

        type_map = {
            "string": "string",
            "text": "string",
            "number": "number",
            "int": "number",
            "integer": "number",
            "float": "number",
            "boolean": "boolean",
            "bool": "boolean",
            "object": "Record<string, any>",
            "dict": "Record<string, any>",
            "array": "any[]",
            "list": "any[]",
            "any": "any",
        }

        return type_map.get(field_type, "any")
