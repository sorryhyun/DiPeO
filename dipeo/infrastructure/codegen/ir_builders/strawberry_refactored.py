"""Refactored Strawberry (GraphQL) IR builder implementation."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Optional

from dipeo.domain.codegen.ir_builder_port import IRBuilderPort, IRData
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
    extract_enums_from_ast,
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
        self.config_root = config_root or Path("projects/codegen/configs")
        self.type_converter = TypeConverter()
        logger.info("Initialized StrawberryIRBuilder with modular architecture")

    def build_ir(self, file_dict: dict[str, Any]) -> IRData:
        """Build IR from TypeScript AST files.

        Args:
            file_dict: Dictionary of AST files

        Returns:
            IRData containing Strawberry GraphQL definitions

        Raises:
            ValueError: If IR building fails
        """
        try:
            logger.debug(f"Processing {len(file_dict)} AST files")

            # Load configuration
            config = StrawberryConfig(self.config_root)
            logger.debug("Loaded Strawberry configuration")

            # Extract data from AST
            operations = extract_operations_from_ast(file_dict, self.type_converter)
            interfaces = extract_interfaces_from_ast(file_dict)
            enums = extract_enums_from_ast(file_dict)
            logger.info(f"Extracted {len(operations)} operations, {len(interfaces)} interfaces")

            # Transform to GraphQL types
            domain_types = transform_domain_types(
                interfaces, config.domain_fields, self.type_converter
            )
            input_types = transform_input_types(operations, self.type_converter)
            result_types = transform_result_types(operations, self.type_converter)
            logger.info(f"Transformed {len(domain_types)} domain types")

            # Build IR structures
            domain_data = build_domain_ir(domain_types, interfaces, enums)
            operations_data = build_operations_ir(operations, input_types, result_types)

            # Create complete IR
            ir_data = build_complete_ir(operations_data, domain_data, config.to_dict())
            logger.info("Successfully built Strawberry IR")

            return ir_data

        except FileNotFoundError as e:
            logger.error(f"Configuration file not found: {e}")
            raise
        except Exception as e:
            logger.error(f"Error building Strawberry IR: {e}")
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

        if not is_valid:
            for error in errors:
                logger.warning(f"Validation error: {error}")

        return is_valid