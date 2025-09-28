"""Domain model extraction and processing module."""

from __future__ import annotations

from typing import Any, Optional

from dipeo.infrastructure.codegen.ir_builders.core import (
    BuildContext,
    BuildStep,
    StepResult,
    StepType,
)
from dipeo.infrastructure.codegen.ir_builders.utils import TypeConverter


class ExtractDomainModelsStep(BuildStep):
    """Step to extract domain models from TypeScript AST."""

    def __init__(self):
        """Initialize domain models extraction step."""
        super().__init__(name="extract_domain_models", step_type=StepType.EXTRACT, required=True)

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Extract domain models from AST data.

        Args:
            context: Build context with utilities
            input_data: TypeScript AST data

        Returns:
            StepResult with extracted domain models
        """
        if not isinstance(input_data, dict):
            return StepResult(success=False, error="Input data must be a dictionary of AST files")

        type_converter = context.type_converter
        domain_models = self._extract_domain_models(input_data, type_converter)

        return StepResult(
            success=True,
            data=domain_models,
            metadata={
                "newtype_count": len(domain_models.get("newtypes", [])),
                "model_count": len(domain_models.get("models", [])),
                "alias_count": len(domain_models.get("aliases", [])),
            },
        )

    def _extract_domain_models(
        self, ast_data: dict[str, Any], type_converter: TypeConverter
    ) -> dict[str, Any]:
        """Extract domain model data from AST.

        Args:
            ast_data: TypeScript AST data
            type_converter: Type converter instance

        Returns:
            Dictionary with newtypes, models, and aliases
        """
        domain_models: dict[str, list[Any]] = {
            "newtypes": [],
            "models": [],
            "aliases": [],
        }

        processed_newtypes: set[str] = set()
        processed_models: set[str] = set()

        # Define domain files to process
        domain_files = [
            "core/diagram.ts",
            "core/execution.ts",
            "core/conversation.ts",
            "core/cli-session.ts",
            "core/file.ts",
            "core/subscription-types.ts",
            "core/integration.ts",
            "claude-code/session-types.ts",
            "codegen/ast-types.ts",
            "frontend/query-specifications.ts",
            "frontend/relationship-queries.ts",
        ]

        for file_path, file_data in ast_data.items():
            # Check if this is a domain file
            is_domain_file = any(file_path.endswith(f"{df}.json") for df in domain_files)
            if not is_domain_file:
                continue

            # Extract newtypes (branded types)
            newtypes = self._extract_newtypes(file_data, type_converter, processed_newtypes)
            domain_models["newtypes"].extend(newtypes)

            # Extract models (interfaces)
            models = self._extract_models(file_data, type_converter, processed_models)
            domain_models["models"].extend(models)

        return domain_models

    def _extract_newtypes(
        self, file_data: dict[str, Any], type_converter: TypeConverter, processed: set[str]
    ) -> list[dict[str, Any]]:
        """Extract branded NewType declarations.

        Args:
            file_data: AST data for a file
            type_converter: Type converter instance
            processed: Set of already processed type names

        Returns:
            List of newtype definitions
        """
        newtypes = []

        for type_alias in file_data.get("types", []):
            type_name = type_alias.get("name", "")
            type_text = type_alias.get("type", "")

            # Check if it's a branded type
            if (
                isinstance(type_text, str)
                and "readonly __brand:" in type_text
                and type_name not in processed
            ):
                base_type = type_text.split(" & ")[0].strip()
                python_base = type_converter.ts_to_python(base_type)
                newtypes.append({"name": type_name, "base": python_base})
                processed.add(type_name)

        return newtypes

    def _extract_models(
        self, file_data: dict[str, Any], type_converter: TypeConverter, processed: set[str]
    ) -> list[dict[str, Any]]:
        """Extract model interfaces.

        Args:
            file_data: AST data for a file
            type_converter: Type converter instance
            processed: Set of already processed model names

        Returns:
            List of model definitions
        """
        models = []

        for interface in file_data.get("interfaces", []):
            interface_name = interface.get("name", "")
            if not interface_name or interface_name in processed:
                continue

            # Skip base/spec interfaces
            if interface_name in {"BaseNodeData", "NodeSpecification"}:
                continue

            processed.add(interface_name)

            # Extract fields
            fields = []
            properties = interface.get("properties", [])
            for prop in properties:
                field = self._convert_property_to_field(prop, type_converter)
                if field:
                    fields.append(field)

            if fields:
                models.append(
                    {
                        "name": interface_name,
                        "fields": fields,
                        "description": interface.get("description", ""),
                    }
                )

        return models

    def _convert_property_to_field(
        self, prop: dict[str, Any], type_converter: TypeConverter
    ) -> Optional[dict[str, Any]]:
        """Convert interface property to field definition.

        Args:
            prop: Property definition from AST
            type_converter: Type converter instance

        Returns:
            Field definition or None
        """
        field_name = prop.get("name")
        if not field_name:
            return None

        ts_type = prop.get("type", "any")
        if isinstance(ts_type, dict):
            ts_type = ts_type.get("text", "any")

        python_type = type_converter.ts_to_python(ts_type)

        return {
            "name": field_name,
            "type": ts_type,
            "python_type": python_type,
            "optional": prop.get("optional", False),
            "description": prop.get("description", ""),
        }


class ExtractEnumsStep(BuildStep):
    """Step to extract enum definitions from TypeScript AST."""

    def __init__(self):
        """Initialize enum extraction step."""
        super().__init__(name="extract_enums", step_type=StepType.EXTRACT, required=True)

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Extract enum definitions from AST data.

        Args:
            context: Build context
            input_data: TypeScript AST data

        Returns:
            StepResult with extracted enums
        """
        if not isinstance(input_data, dict):
            return StepResult(success=False, error="Input data must be a dictionary of AST files")

        enums = self._extract_enums(input_data)

        return StepResult(success=True, data=enums, metadata={"enum_count": len(enums)})

    def _extract_enums(self, ast_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract all enum definitions from TypeScript AST.

        Args:
            ast_data: Dictionary of AST files

        Returns:
            List of enum definitions
        """
        enums = []
        processed_enums = set()

        for _file_path, file_data in ast_data.items():
            for enum in file_data.get("enums", []):
                enum_name = enum.get("name", "")

                # Skip if already processed
                if enum_name in processed_enums:
                    continue

                processed_enums.add(enum_name)

                # Extract enum values
                values = self._extract_enum_values(enum)

                enum_def = {
                    "name": enum_name,
                    "values": values,
                    "description": enum.get("description", ""),
                }
                enums.append(enum_def)

        return enums

    def _extract_enum_values(self, enum: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract values from enum definition.

        Args:
            enum: Enum definition from AST

        Returns:
            List of enum value definitions
        """
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

        return values


class ExtractIntegrationsStep(BuildStep):
    """Step to extract integration definitions from TypeScript AST."""

    def __init__(self):
        """Initialize integrations extraction step."""
        super().__init__(name="extract_integrations", step_type=StepType.EXTRACT, required=False)

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Extract integration definitions from AST data.

        Args:
            context: Build context
            input_data: TypeScript AST data

        Returns:
            StepResult with extracted integrations
        """
        if not isinstance(input_data, dict):
            return StepResult(success=False, error="Input data must be a dictionary of AST files")

        integrations = self._extract_integrations(input_data)

        return StepResult(
            success=True, data=integrations, metadata={"integration_count": len(integrations)}
        )

    def _extract_integrations(self, ast_data: dict[str, Any]) -> list[dict[str, Any]]:
        """Extract integration definitions from TypeScript AST.

        Args:
            ast_data: Dictionary of AST files

        Returns:
            List of integration definitions
        """
        integrations = []
        processed = set()

        for file_path, file_data in ast_data.items():
            # Look for integration-related files
            if "integration" not in file_path.lower():
                continue

            # Extract from constants
            for const in file_data.get("constants", []):
                const_name = const.get("name", "")
                if "Integration" in const_name and const_name not in processed:
                    integration = {
                        "name": const_name,
                        "value": const.get("value", {}),
                        "type": const.get("type", ""),
                    }
                    integrations.append(integration)
                    processed.add(const_name)

            # Extract from types
            for type_def in file_data.get("types", []):
                type_name = type_def.get("name", "")
                if "Integration" in type_name and type_name not in processed:
                    integration = {
                        "name": type_name,
                        "definition": type_def,
                    }
                    integrations.append(integration)
                    processed.add(type_name)

        return integrations


class ExtractConversionsStep(BuildStep):
    """Step to extract type conversion data from TypeScript AST."""

    def __init__(self):
        """Initialize conversions extraction step."""
        super().__init__(name="extract_conversions", step_type=StepType.EXTRACT, required=False)

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Extract conversion data from AST data.

        Args:
            context: Build context
            input_data: TypeScript AST data

        Returns:
            StepResult with extracted conversions
        """
        if not isinstance(input_data, dict):
            return StepResult(success=False, error="Input data must be a dictionary of AST files")

        conversions = self._extract_conversions(input_data)

        return StepResult(
            success=True, data=conversions, metadata={"conversion_count": len(conversions)}
        )

    def _extract_conversions(self, ast_data: dict[str, Any]) -> dict[str, Any]:
        """Extract conversion data from TypeScript AST.

        Args:
            ast_data: Dictionary of AST files

        Returns:
            Dictionary with conversion data
        """
        conversions = {
            "type_mappings": [],
            "enum_mappings": [],
        }

        for file_path, file_data in ast_data.items():
            # Look for conversion-related files
            if "conversion" not in file_path.lower() and "mapping" not in file_path.lower():
                continue

            # Extract type mappings from constants
            for const in file_data.get("constants", []):
                const_name = const.get("name", "")
                if "Mapping" in const_name or "Conversion" in const_name:
                    conversions["type_mappings"].append(
                        {
                            "name": const_name,
                            "value": const.get("value", {}),
                        }
                    )

        return conversions
