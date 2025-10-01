"""Zod schema generation module for runtime validation."""

from __future__ import annotations

from pathlib import Path
from typing import Any

from dipeo.infrastructure.codegen.ir_builders.core import (
    BuildContext,
    BuildStep,
    StepResult,
    StepType,
)
from dipeo.infrastructure.codegen.ir_builders.type_system_unified import UnifiedTypeConverter


class GenerateZodSchemasStep(BuildStep):
    """Generate Zod schemas from node specifications for runtime validation."""

    def __init__(self):
        """Initialize Zod schema generation step."""
        super().__init__(name="generate_zod_schemas", step_type=StepType.TRANSFORM, required=False)
        self._dependencies = ["extract_node_specs", "extract_enums"]

    def execute(self, context: BuildContext, input_data: Any) -> StepResult:
        """Generate Zod schemas from node specifications.

        Args:
            context: Build context with config and utilities
            input_data: Input data (unused, we get data from context)

        Returns:
            StepResult with generated Zod schemas
        """
        try:
            # Get node specs and enums from context
            node_specs = context.get_step_data("extract_node_specs") or []
            enums = context.get_step_data("extract_enums") or []

            type_converter = context.type_converter

            # Generate schemas for each node type
            schemas = []
            for spec in node_specs:
                schema = self._generate_node_schema(spec, type_converter)
                if schema:
                    schemas.append(schema)

            # Generate enum schemas
            enum_schemas = []
            for enum in enums:
                enum_schema = self._generate_enum_schema(enum)
                if enum_schema:
                    enum_schemas.append(enum_schema)

            result_data = {
                "node_schemas": schemas,
                "enum_schemas": enum_schemas,
                "metadata": {
                    "node_count": len(schemas),
                    "enum_count": len(enum_schemas),
                },
            }

            return StepResult(
                success=True,
                data=result_data,
                metadata={
                    "node_count": len(schemas),
                    "enum_count": len(enum_schemas),
                },
            )

        except Exception as e:
            return StepResult(
                success=False,
                error=f"Failed to generate Zod schemas: {e}",
            )

    def _generate_node_schema(
        self, spec: dict[str, Any], type_converter: UnifiedTypeConverter
    ) -> dict[str, Any] | None:
        """Generate Zod schema for a node specification.

        Args:
            spec: Node specification data
            type_converter: Type converter for TypeScript to Zod mapping

        Returns:
            Dictionary with schema name and fields, or None if invalid
        """
        node_type = spec.get("node_type")
        node_name = spec.get("node_name")
        fields = spec.get("fields", [])

        if not node_type or not node_name:
            return None

        # Generate field schemas
        field_schemas = []
        for field in fields:
            field_schema = self._generate_field_schema(field, type_converter)
            if field_schema:
                field_schemas.append(field_schema)

        return {
            "node_type": node_type,
            "node_name": node_name,
            "schema_name": f"{node_name}Schema",
            "fields": field_schemas,
            "description": spec.get("description", ""),
        }

    def _generate_field_schema(
        self, field: dict[str, Any], type_converter: UnifiedTypeConverter
    ) -> dict[str, Any] | None:
        """Generate Zod schema for a field.

        Args:
            field: Field specification
            type_converter: Type converter instance

        Returns:
            Dictionary with field schema information
        """
        field_name = field.get("name")
        field_type = field.get("type", "any")
        required = field.get("required", False)
        description = field.get("description", "")
        validation = field.get("validation", {})

        if not field_name:
            return None

        # Convert TypeScript type to Zod type
        zod_type = self._ts_type_to_zod_type(field_type, validation)

        # Handle optional fields
        if not required:
            zod_type = f"{zod_type}.optional()"

        # Add validation rules
        zod_type = self._add_validation_rules(zod_type, field_type, validation)

        # Add description
        if description:
            zod_type = f'{zod_type}.describe("{description}")'

        return {
            "name": field_name,
            "type": field_type,
            "zod_type": zod_type,
            "required": required,
            "description": description,
            "validation": validation,
        }

    def _ts_type_to_zod_type(self, ts_type: str, validation: dict[str, Any]) -> str:
        """Convert TypeScript type to Zod type.

        Args:
            ts_type: TypeScript type string
            validation: Validation rules

        Returns:
            Zod type string
        """
        # Handle array types
        if ts_type.endswith("[]"):
            base_type = ts_type[:-2]
            element_type = self._ts_type_to_zod_type(base_type, {})
            return f"z.array({element_type})"

        # Handle enum types
        if ts_type == "enum" and "allowedValues" in validation:
            values = validation["allowedValues"]
            if values:
                # Create union of literals
                literals = ", ".join([f'z.literal("{v}")' for v in values])
                return f"z.union([{literals}])"
            return "z.string()"

        # Basic type mappings
        type_map = {
            "string": "z.string()",
            "number": "z.number()",
            "boolean": "z.boolean()",
            "object": "z.record(z.any())",
            "array": "z.array(z.any())",
            "any": "z.any()",
            "null": "z.null()",
            "undefined": "z.undefined()",
        }

        return type_map.get(ts_type, "z.any()")

    def _add_validation_rules(
        self, zod_type: str, field_type: str, validation: dict[str, Any]
    ) -> str:
        """Add validation rules to Zod type.

        Args:
            zod_type: Base Zod type
            field_type: Field type
            validation: Validation rules

        Returns:
            Zod type with validation rules
        """
        # String validation
        if field_type == "string":
            if "minLength" in validation:
                zod_type = f"{zod_type}.min({validation['minLength']})"
            if "maxLength" in validation:
                zod_type = f"{zod_type}.max({validation['maxLength']})"
            if "pattern" in validation:
                pattern = validation["pattern"].replace("\\", "\\\\").replace('"', '\\"')
                zod_type = f'{zod_type}.regex(/{pattern}/)'
            if "format" in validation:
                fmt = validation["format"]
                if fmt == "email":
                    zod_type = f"{zod_type}.email()"
                elif fmt == "url":
                    zod_type = f"{zod_type}.url()"
                elif fmt == "uuid":
                    zod_type = f"{zod_type}.uuid()"

        # Number validation
        elif field_type == "number":
            if "min" in validation:
                zod_type = f"{zod_type}.min({validation['min']})"
            if "max" in validation:
                zod_type = f"{zod_type}.max({validation['max']})"
            if "integer" in validation and validation["integer"]:
                zod_type = f"{zod_type}.int()"

        # Array validation
        elif field_type.endswith("[]") or field_type == "array":
            if "minItems" in validation:
                zod_type = f"{zod_type}.min({validation['minItems']})"
            if "maxItems" in validation:
                zod_type = f"{zod_type}.max({validation['maxItems']})"

        return zod_type

    def _generate_enum_schema(self, enum: dict[str, Any]) -> dict[str, Any] | None:
        """Generate Zod schema for an enum.

        Args:
            enum: Enum specification

        Returns:
            Dictionary with enum schema information
        """
        enum_name = enum.get("name")
        values = enum.get("values", [])

        if not enum_name or not values:
            return None

        # Generate Zod enum
        if isinstance(values, list):
            if all(isinstance(v, str) for v in values):
                # String enum
                enum_values = ", ".join([f'"{v}"' for v in values])
                zod_enum = f"z.enum([{enum_values}])"
            else:
                # Mixed enum - use union of literals
                literals = []
                for v in values:
                    if isinstance(v, str):
                        literals.append(f'z.literal("{v}")')
                    elif isinstance(v, (int, float)):
                        literals.append(f"z.literal({v})")
                    elif isinstance(v, bool):
                        literals.append(f"z.literal({str(v).lower()})")
                zod_enum = f"z.union([{', '.join(literals)}])"
        else:
            # Fallback to string
            zod_enum = "z.string()"

        return {
            "name": enum_name,
            "schema_name": f"{enum_name}Schema",
            "zod_enum": zod_enum,
            "values": values,
        }
