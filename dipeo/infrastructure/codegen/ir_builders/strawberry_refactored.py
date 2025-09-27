"""Refactored Strawberry (GraphQL) IR builder implementation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from dipeo.domain.codegen.ir_builder_port import IRBuilderPort, IRData
from dipeo.infrastructure.codegen.ir_builders.backend_extractors import (
    extract_node_specs,
)
from dipeo.infrastructure.codegen.ir_builders.base import BaseIRBuilder
from dipeo.infrastructure.codegen.ir_builders.strawberry_builders import (
    build_complete_ir,
    build_domain_ir,
    build_operations_ir,
    validate_strawberry_ir,
)
from dipeo.infrastructure.codegen.ir_builders.strawberry_config import StrawberryConfig
from dipeo.infrastructure.codegen.ir_builders.strawberry_extractors import (
    extract_operations_from_ast,
)
from dipeo.infrastructure.codegen.ir_builders.strawberry_transformers import (
    transform_domain_types,
    transform_input_types,
    transform_result_types,
)
from dipeo.infrastructure.codegen.ir_builders.utils import (
    TypeConverter,
    extract_branded_scalars_from_ast,
    extract_enums_from_ast,
    extract_graphql_input_types_from_ast,
    extract_interfaces_from_ast,
)

logger = logging.getLogger(__name__)


class StrawberryIRBuilder(BaseIRBuilder, IRBuilderPort):
    """IR builder for Strawberry GraphQL code generation.

    This refactored version uses modular components for better maintainability:
    - StrawberryConfig: Configuration management
    - strawberry_extractors: Operation extraction from AST
    - strawberry_transformers: Type transformations
    - strawberry_builders: IR building and validation
    """

    def __init__(self, config_root: Optional[Path] = None):
        """Initialize Strawberry IR builder.

        Args:
            config_root: Root path for configuration files
        """
        super().__init__()
        # Try default config path or fallback to None for no config
        if config_root:
            self.config_root = config_root
        else:
            # Try original default location first
            default_path = Path("projects/codegen/config/strawberry")
            if default_path.exists():
                self.config_root = default_path
            else:
                self.config_root = None
        self.type_converter = TypeConverter()
        # logger.info("Initialized StrawberryIRBuilder with modular architecture")

    async def build_ir(self, file_dict: dict[str, Any]) -> IRData:
        """Build IR from TypeScript AST files.

        Args:
            file_dict: Dictionary of AST files

        Returns:
            IRData containing Strawberry GraphQL definitions

        Raises:
            ValueError: If IR building fails
        """
        try:
            # logger.debug(f"Processing {len(file_dict)} AST files")

            # Load configuration or use defaults
            if self.config_root:
                try:
                    config = StrawberryConfig(self.config_root)
                    # logger.debug("Loaded Strawberry configuration")
                    config_dict = config.to_dict()
                    domain_fields = config.domain_fields
                except FileNotFoundError:
                    # logger.warning("Configuration files not found, using defaults")
                    config_dict = {"type_mappings": {}, "domain_fields": {}, "schema": {}}
                    domain_fields = {}
            else:
                # logger.debug("No config root specified, using defaults")
                config_dict = {"type_mappings": {}, "domain_fields": {}, "schema": {}}
                domain_fields = {}

            # Extract data from AST
            operations = extract_operations_from_ast(file_dict, self.type_converter)
            interfaces = extract_interfaces_from_ast(file_dict)
            raw_enums = extract_enums_from_ast(file_dict)
            scalars = extract_branded_scalars_from_ast(file_dict)
            graphql_inputs = extract_graphql_input_types_from_ast(file_dict)

            # Transform enums to have values field instead of members
            enums = []
            for enum in raw_enums:
                values = []
                for member in enum.get("members", []):
                    if isinstance(member, dict):
                        values.append(
                            {
                                "name": member.get("name", ""),
                                "value": member.get("value", member.get("name", "").lower()),
                            }
                        )
                    else:
                        # If member is a string
                        values.append({"name": str(member), "value": str(member).lower()})
                enums.append(
                    {
                        "name": enum.get("name", ""),
                        "values": values,
                        "description": enum.get("description", ""),
                        "file": enum.get("file", ""),
                    }
                )
            node_specs = extract_node_specs(file_dict, self.type_converter)
            # logger.info(
            #     f"Extracted {len(operations)} operations, {len(interfaces)} interfaces, "
            #     f"{len(node_specs)} node specs"
            # )

            # Transform to GraphQL types
            domain_types = transform_domain_types(interfaces, domain_fields, self.type_converter)
            input_types = transform_input_types(operations, self.type_converter)
            result_types = transform_result_types(operations, self.type_converter)
            # logger.info(f"Transformed {len(domain_types)} domain types")

            # Build IR structures
            domain_data = build_domain_ir(domain_types, interfaces, enums, scalars, graphql_inputs)
            operations_data = build_operations_ir(operations, input_types, result_types)

            # Create complete IR with scalars included
            ir_data = build_complete_ir(
                operations_data, domain_data, config_dict, list(file_dict.keys()), node_specs
            )
            # logger.info("Successfully built Strawberry IR")

            return ir_data

        except FileNotFoundError as e:
            # logger.error(f"Configuration file not found: {e}")
            raise
        except Exception as e:
            # logger.error(f"Error building Strawberry IR: {e}")
            raise ValueError(f"Failed to build Strawberry IR: {e}")

    def validate_ir(self, ir_data: IRData) -> bool:
        """Validate Strawberry IR data.

        Args:
            ir_data: IR data to validate

        Returns:
            True if validation passes
        """
        # Check basic structure
        if not super().validate_ir(ir_data):
            return False

        # Perform Strawberry-specific validation
        is_valid, errors = validate_strawberry_ir(ir_data)

        # if not is_valid:
        #     for error in errors:
        # logger.warning(f"Validation error: {error}")

        return is_valid
