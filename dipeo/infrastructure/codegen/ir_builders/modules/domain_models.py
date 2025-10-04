"""Domain model extraction and processing module."""

from __future__ import annotations

from typing import Any, Optional

from dipeo.infrastructure.codegen.ir_builders.core import (
    BaseExtractionStep,
    BuildContext,
    BuildStep,
    StepResult,
    StepType,
)
from dipeo.infrastructure.codegen.ir_builders.type_system_unified import UnifiedTypeConverter


class ExtractDomainModelsStep(BaseExtractionStep):
    """Step to extract domain models from TypeScript AST."""

    # Define domain files to process
    DOMAIN_FILES = [
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

    def __init__(self):
        """Initialize domain models extraction step."""
        super().__init__(name="extract_domain_models", required=True)
        self._processed_newtypes: set[str] = set()
        self._processed_models: set[str] = set()
        self._all_newtypes: list[dict[str, Any]] = []
        self._all_models: list[dict[str, Any]] = []

    def pre_extraction_hook(self, context: BuildContext, input_data: dict[str, Any]) -> None:
        """Reset processing state before extraction."""
        self._processed_newtypes = set()
        self._processed_models = set()
        self._all_newtypes = []
        self._all_models = []

    def should_process_file(self, file_path: str, file_data: dict[str, Any]) -> bool:
        """Filter to only process domain model files."""
        return any(file_path.endswith(f"{df}.json") for df in self.DOMAIN_FILES)

    def extract_from_file(
        self,
        file_path: str,
        file_data: dict[str, Any],
        type_converter: UnifiedTypeConverter,
        context: BuildContext,
    ) -> None:
        """Extract domain models from a single AST file.

        Args:
            file_path: Path to the AST file
            file_data: AST data for the file
            type_converter: Type converter instance
            context: Build context

        Returns:
            None (accumulates data in instance variables)
        """
        # Extract newtypes (branded types)
        newtypes = self._extract_newtypes(file_data, type_converter, self._processed_newtypes)
        self._all_newtypes.extend(newtypes)

        # Extract models (interfaces)
        models = self._extract_models(file_data, type_converter, self._processed_models)
        self._all_models.extend(models)

    def post_extraction_hook(
        self, extracted_data: list[Any], context: BuildContext
    ) -> dict[str, Any]:
        """Assemble domain models data after extraction.

        Args:
            extracted_data: Unused (data accumulated in instance variables)
            context: Build context

        Returns:
            Dictionary with newtypes, models, and aliases
        """
        return {
            "newtypes": self._all_newtypes,
            "models": self._all_models,
            "aliases": [],  # Kept for compatibility
        }

    def get_metadata(self, extracted_data: Any) -> dict[str, Any]:
        """Generate metadata for extraction result.

        Args:
            extracted_data: Dictionary with extracted domain models

        Returns:
            Metadata dictionary
        """
        if isinstance(extracted_data, dict):
            return {
                "newtype_count": len(extracted_data.get("newtypes", [])),
                "model_count": len(extracted_data.get("models", [])),
                "alias_count": len(extracted_data.get("aliases", [])),
            }
        return {"newtype_count": 0, "model_count": 0, "alias_count": 0}

    def _extract_newtypes(
        self, file_data: dict[str, Any], type_converter: UnifiedTypeConverter, processed: set[str]
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
        self, file_data: dict[str, Any], type_converter: UnifiedTypeConverter, processed: set[str]
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
        self, prop: dict[str, Any], type_converter: UnifiedTypeConverter
    ) -> dict[str, Any] | None:
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


class ExtractEnumsStep(BaseExtractionStep):
    """Step to extract enum definitions from TypeScript AST."""

    def __init__(self):
        """Initialize enum extraction step."""
        super().__init__(name="extract_enums", required=True)
        self._processed_enums: set[str] = set()

    def pre_extraction_hook(self, context: BuildContext, input_data: dict[str, Any]) -> None:
        """Reset processing state before extraction."""
        self._processed_enums = set()

    def extract_from_file(
        self,
        file_path: str,
        file_data: dict[str, Any],
        type_converter: UnifiedTypeConverter,
        context: BuildContext,
    ) -> list[dict[str, Any]]:
        """Extract enum definitions from a single AST file.

        Args:
            file_path: Path to the AST file
            file_data: AST data for the file
            type_converter: Type converter instance
            context: Build context

        Returns:
            List of enum definitions from this file
        """
        enums = []
        for enum in file_data.get("enums", []):
            enum_name = enum.get("name", "")

            # Skip if already processed
            if enum_name in self._processed_enums:
                continue

            self._processed_enums.add(enum_name)

            # Extract enum values
            values = self._extract_enum_values(enum)

            enum_def = {
                "name": enum_name,
                "values": values,
                "description": enum.get("description", ""),
            }
            enums.append(enum_def)

        return enums

    def get_metadata(self, extracted_data: list[Any]) -> dict[str, Any]:
        """Generate metadata for extraction result.

        Args:
            extracted_data: Extracted enums

        Returns:
            Metadata dictionary
        """
        return {"enum_count": len(extracted_data)}

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


class ExtractIntegrationsStep(BaseExtractionStep):
    """Step to extract integration definitions from TypeScript AST."""

    def __init__(self):
        """Initialize integrations extraction step."""
        super().__init__(name="extract_integrations", required=False)
        self._processed: set[str] = set()

    def pre_extraction_hook(self, context: BuildContext, input_data: dict[str, Any]) -> None:
        """Reset processing state before extraction."""
        self._processed = set()

    def should_process_file(self, file_path: str, file_data: dict[str, Any]) -> bool:
        """Filter to only process integration-related files."""
        return "integration" in file_path.lower()

    def extract_from_file(
        self,
        file_path: str,
        file_data: dict[str, Any],
        type_converter: UnifiedTypeConverter,
        context: BuildContext,
    ) -> list[dict[str, Any]]:
        """Extract integration definitions from a single AST file.

        Args:
            file_path: Path to the AST file
            file_data: AST data for the file
            type_converter: Type converter instance
            context: Build context

        Returns:
            List of integration definitions from this file
        """
        integrations = []

        # Extract from constants
        for const in file_data.get("constants", []):
            const_name = const.get("name", "")
            if "Integration" in const_name and const_name not in self._processed:
                integration = {
                    "name": const_name,
                    "value": const.get("value", {}),
                    "type": const.get("type", ""),
                }
                integrations.append(integration)
                self._processed.add(const_name)

        # Extract from types
        for type_def in file_data.get("types", []):
            type_name = type_def.get("name", "")
            if "Integration" in type_name and type_name not in self._processed:
                integration = {
                    "name": type_name,
                    "definition": type_def,
                }
                integrations.append(integration)
                self._processed.add(type_name)

        return integrations

    def get_metadata(self, extracted_data: list[Any]) -> dict[str, Any]:
        """Generate metadata for extraction result.

        Args:
            extracted_data: Extracted integrations

        Returns:
            Metadata dictionary
        """
        return {"integration_count": len(extracted_data)}


class ExtractConversionsStep(BaseExtractionStep):
    """Step to extract type conversion data from TypeScript AST."""

    def __init__(self):
        """Initialize conversions extraction step."""
        super().__init__(name="extract_conversions", required=False)
        self._type_mappings: list[dict[str, Any]] = []
        self._enum_mappings: list[dict[str, Any]] = []

    def pre_extraction_hook(self, context: BuildContext, input_data: dict[str, Any]) -> None:
        """Reset processing state before extraction."""
        self._type_mappings = []
        self._enum_mappings = []

    def should_process_file(self, file_path: str, file_data: dict[str, Any]) -> bool:
        """Filter to only process conversion-related files."""
        return "conversion" in file_path.lower() or "mapping" in file_path.lower()

    def extract_from_file(
        self,
        file_path: str,
        file_data: dict[str, Any],
        type_converter: UnifiedTypeConverter,
        context: BuildContext,
    ) -> None:
        """Extract conversion data from a single AST file.

        Args:
            file_path: Path to the AST file
            file_data: AST data for the file
            type_converter: Type converter instance
            context: Build context

        Returns:
            None (accumulates data in instance variables)
        """
        # Extract type mappings from constants
        for const in file_data.get("constants", []):
            const_name = const.get("name", "")
            if "Mapping" in const_name or "Conversion" in const_name:
                self._type_mappings.append(
                    {
                        "name": const_name,
                        "value": const.get("value", {}),
                    }
                )

    def post_extraction_hook(
        self, extracted_data: list[Any], context: BuildContext
    ) -> dict[str, Any]:
        """Assemble conversions data after extraction.

        Args:
            extracted_data: Unused (data accumulated in instance variables)
            context: Build context

        Returns:
            Dictionary with type_mappings and enum_mappings
        """
        return {
            "type_mappings": self._type_mappings,
            "enum_mappings": self._enum_mappings,
        }

    def get_metadata(self, extracted_data: Any) -> dict[str, Any]:
        """Generate metadata for extraction result.

        Args:
            extracted_data: Dictionary with extracted conversions

        Returns:
            Metadata dictionary
        """
        if isinstance(extracted_data, dict):
            return {
                "conversion_count": len(extracted_data.get("type_mappings", []))
                + len(extracted_data.get("enum_mappings", []))
            }
        return {"conversion_count": 0}
