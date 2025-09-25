"""Refactored Backend IR builder implementation."""

from __future__ import annotations

import logging
from datetime import datetime
from typing import Any

from dipeo.domain.codegen.ir_builder_port import IRBuilderPort, IRData
from dipeo.infrastructure.codegen.ir_builders.backend_builders import (
    build_factory_data,
    build_models_data,
)
from dipeo.infrastructure.codegen.ir_builders.backend_extractors import (
    extract_enums_all,
    extract_models,
    extract_node_specs,
)
from dipeo.infrastructure.codegen.ir_builders.base import BaseIRBuilder
from dipeo.infrastructure.codegen.ir_builders.utils import TypeConverter

logger = logging.getLogger(__name__)


class BackendIRBuilder(BaseIRBuilder, IRBuilderPort):
    """IR builder for backend code generation.

    This refactored version uses modular components for better maintainability:
    - backend_extractors: Extract node specs, enums, and models from AST
    - backend_builders: Build factory and model data structures
    """

    def __init__(self):
        """Initialize Backend IR builder."""
        super().__init__()
        self.type_converter = TypeConverter()
        logger.info("Initialized BackendIRBuilder with modular architecture")

    def build_ir(self, file_dict: dict[str, Any]) -> IRData:
        """Build IR from TypeScript AST files.

        Args:
            file_dict: Dictionary of AST files

        Returns:
            IRData containing backend definitions

        Raises:
            ValueError: If IR building fails
        """
        try:
            logger.debug(f"Processing {len(file_dict)} AST files")

            # Extract data from AST
            node_specs = extract_node_specs(file_dict, self.type_converter)
            enums = extract_enums_all(file_dict)
            models = extract_models(file_dict)

            logger.info(
                f"Extracted {len(node_specs)} node specs, "
                f"{len(enums)} enums, {len(models)} models"
            )

            # Build data structures
            factory_data = build_factory_data(node_specs)
            models_data = build_models_data(models, enums)

            # Create backend IR
            backend_data = {
                "node_specs": node_specs,
                "enums": enums,
                "models": models_data["interfaces"],
                "type_aliases": models_data["type_aliases"],
                "factory": factory_data,
                "metadata": {
                    "generated_at": datetime.now().isoformat(),
                    "node_count": len(node_specs),
                    "enum_count": len(enums),
                    "model_count": len(models),
                },
            }

            # Create IR data
            ir_data = IRData(
                backend=backend_data,
                frontend={},  # Empty for backend-only build
                strawberry={},  # Empty for backend-only build
            )

            logger.info("Successfully built Backend IR")
            return ir_data

        except Exception as e:
            logger.error(f"Error building Backend IR: {e}")
            raise ValueError(f"Failed to build Backend IR: {e}")

    def validate_ir(self, ir_data: IRData) -> bool:
        """Validate Backend IR data.

        Args:
            ir_data: IR data to validate

        Returns:
            True if validation passes
        """
        # Check basic structure
        if not super().validate_ir(ir_data):
            return False

        if not ir_data.backend:
            logger.warning("Backend data is missing")
            return False

        backend_data = ir_data.backend

        # Check required fields
        required_keys = ["node_specs", "enums", "models", "factory"]
        for key in required_keys:
            if key not in backend_data:
                logger.warning(f"Missing required key in backend data: {key}")
                return False

        # Validate node specs
        node_specs = backend_data.get("node_specs", [])
        if not node_specs:
            logger.warning("No node specifications found")
            return False

        for spec in node_specs:
            if not spec.get("node_type"):
                logger.warning("Node spec missing node_type")
                return False
            if not spec.get("fields"):
                logger.warning(f"Node spec {spec.get('node_type')} has no fields")
                return False

        # Validate factory data
        factory = backend_data.get("factory", {})
        if not factory.get("mappings"):
            logger.warning("Factory mappings are empty")
            return False

        logger.info("Backend IR validation passed")
        return True