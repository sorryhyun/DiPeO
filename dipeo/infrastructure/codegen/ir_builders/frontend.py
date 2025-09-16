"""Frontend IR builder implementation."""

import os
import sys
from pathlib import Path
from typing import Any, Optional

# Add DiPeO base directory to path for imports
sys.path.append(os.environ.get("DIPEO_BASE_DIR", "/home/soryhyun/DiPeO"))

from dipeo.domain.codegen.ir_builder_port import IRData
from dipeo.infrastructure.codegen.ir_builders.base import BaseIRBuilder


class FrontendIRBuilder(BaseIRBuilder):
    """Build IR for frontend code generation."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize frontend IR builder.

        Args:
            config_path: Optional path to configuration file
        """
        super().__init__(config_path or "projects/codegen/config/frontend")
        # Import the actual implementation lazily
        from projects.codegen.code.frontend_ir_builder import (
            build_frontend_ir as _build_frontend_ir,
        )

        self._build_frontend_ir = _build_frontend_ir

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
        # Wrap source_data in 'default' key if not already wrapped
        # The frontend_ir_builder expects data under 'default' key
        if "default" not in source_data:
            wrapped_data = {"default": source_data}
        else:
            wrapped_data = source_data

        # Call the existing frontend IR builder
        ir_dict = self._build_frontend_ir(wrapped_data)

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
        data = ir_data.data
        required_keys = ["components", "schemas", "metadata"]

        for key in required_keys:
            if key not in data:
                return False

        # Validate metadata
        if "component_count" not in data.get("metadata", {}):
            return False

        return True
