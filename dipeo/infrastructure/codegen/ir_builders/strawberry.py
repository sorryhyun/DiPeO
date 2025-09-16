"""Strawberry (GraphQL) IR builder implementation."""

import os
import sys
from pathlib import Path
from typing import Any, Optional

# Add DiPeO base directory to path for imports
sys.path.append(os.environ.get("DIPEO_BASE_DIR", "/home/soryhyun/DiPeO"))

from dipeo.domain.codegen.ir_builder_port import IRData
from dipeo.infrastructure.codegen.ir_builders.base import BaseIRBuilder


class StrawberryIRBuilder(BaseIRBuilder):
    """Build IR for GraphQL/Strawberry code generation."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize strawberry IR builder.

        Args:
            config_path: Optional path to configuration file
        """
        super().__init__(config_path or "projects/codegen/config/strawberry")
        # Import the actual implementation lazily
        from projects.codegen.code.strawberry_ir_builder import (
            build_unified_ir as _build_strawberry_ir,
        )

        self._build_strawberry_ir = _build_strawberry_ir

    async def build_ir(
        self, source_data: dict[str, Any], config: Optional[dict[str, Any]] = None
    ) -> IRData:
        """Build IR from source data.

        Args:
            source_data: Input AST data to build IR from
            config: Optional configuration parameters

        Returns:
            IRData containing the built strawberry IR
        """
        # Wrap source_data in 'default' key if not already wrapped
        # The strawberry_ir_builder expects data under 'default' key
        if "default" not in source_data:
            wrapped_data = {"default": source_data}
        else:
            wrapped_data = source_data

        # Call the existing strawberry IR builder
        ir_dict = self._build_strawberry_ir(wrapped_data)

        # Create metadata
        metadata = self.create_metadata(source_data, "strawberry")

        # Return wrapped IR data
        return IRData(metadata=metadata, data=ir_dict)

    def validate_ir(self, ir_data: IRData) -> bool:
        """Validate strawberry IR structure.

        Args:
            ir_data: IR data to validate

        Returns:
            True if valid, False otherwise
        """
        if not super().validate_ir(ir_data):
            return False

        # Check for required strawberry fields
        # Note: Updated to match actual IR structure from strawberry_ir_builder.py
        data = ir_data.data
        required_keys = ["operations", "scalars", "types", "inputs", "enums"]
        # Also accept alternative keys for backward compatibility
        alternative_keys = {
            "types": "domain_types",  # types or domain_types
            "result_wrappers": "results",  # result_wrappers or results
        }

        for key in required_keys:
            if key not in data:
                # Check if alternative key exists
                alt_key = alternative_keys.get(key)
                if (alt_key and alt_key not in data) or not alt_key:
                    return False

        # Validate operations have required fields
        operations = data.get("operations", [])
        if not isinstance(operations, list):
            return False

        return True
