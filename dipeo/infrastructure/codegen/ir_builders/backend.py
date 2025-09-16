"""Backend IR builder implementation."""

import os
import sys
from pathlib import Path
from typing import Any, Optional

# Add DiPeO base directory to path for imports
sys.path.append(os.environ.get("DIPEO_BASE_DIR", "/home/soryhyun/DiPeO"))

from dipeo.domain.codegen.ir_builder_port import IRData
from dipeo.infrastructure.codegen.ir_builders.base import BaseIRBuilder


class BackendIRBuilder(BaseIRBuilder):
    """Build IR for backend code generation."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize backend IR builder.

        Args:
            config_path: Optional path to configuration file
        """
        super().__init__(config_path or "projects/codegen/config/backend")
        # Import the actual implementation lazily
        from projects.codegen.code.backend_ir_builder import build_backend_ir as _build_backend_ir

        self._build_backend_ir = _build_backend_ir

    async def build_ir(
        self, source_data: dict[str, Any], config: Optional[dict[str, Any]] = None
    ) -> IRData:
        """Build IR from source data.

        Args:
            source_data: Input AST data to build IR from
            config: Optional configuration parameters

        Returns:
            IRData containing the built backend IR
        """
        # Wrap source_data in 'default' key if not already wrapped
        # The backend_ir_builder expects data under 'default' key
        if "default" not in source_data:
            wrapped_data = {"default": source_data}
        else:
            wrapped_data = source_data

        # Debug logging
        import logging

        logger = logging.getLogger(__name__)
        logger.info(f"BackendIRBuilder: Processing {len(source_data)} source files")
        logger.info(f"BackendIRBuilder: Keys in source_data: {list(source_data.keys())[:5]}")
        logger.info(f"BackendIRBuilder: Wrapped data keys: {list(wrapped_data.keys())}")

        # Call the existing backend IR builder
        ir_dict = self._build_backend_ir(wrapped_data)

        # Create metadata
        metadata = self.create_metadata(source_data, "backend")

        # Return wrapped IR data
        return IRData(metadata=metadata, data=ir_dict)

    def validate_ir(self, ir_data: IRData) -> bool:
        """Validate backend IR structure.

        Args:
            ir_data: IR data to validate

        Returns:
            True if valid, False otherwise
        """
        if not super().validate_ir(ir_data):
            return False

        # Check for required backend fields
        data = ir_data.data
        required_keys = ["node_specs", "enums", "metadata"]

        for key in required_keys:
            if key not in data:
                return False

        # Validate metadata
        if "node_count" not in data.get("metadata", {}):
            return False

        return True
