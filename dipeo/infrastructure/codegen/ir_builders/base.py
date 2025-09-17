"""Base implementation for IR builders."""

import hashlib
import json
from abc import ABC
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from dipeo.domain.codegen.ir_builder_port import IRBuilderPort, IRData, IRMetadata


class BaseIRBuilder(IRBuilderPort, ABC):
    """Base implementation for IR builders."""

    def __init__(self, config_path: Optional[str] = None):
        """Initialize base IR builder.

        Args:
            config_path: Optional path to configuration file
        """
        self.config_path = config_path
        self.config = self._load_config() if config_path else {}

    def _load_config(self) -> dict[str, Any]:
        """Load configuration from YAML files.

        Returns:
            Configuration dictionary
        """
        if not self.config_path:
            return {}

        config_file = Path(self.config_path)
        if not config_file.exists():
            return {}

        if config_file.is_dir():
            # Load all YAML files in the directory
            config = {}
            for yaml_file in config_file.glob("*.yaml"):
                with open(yaml_file) as f:
                    file_config = yaml.safe_load(f) or {}
                    config.update(file_config)
            return config
        else:
            # Load single YAML file
            with open(config_file) as f:
                return yaml.safe_load(f) or {}

    def get_cache_key(self, source_data: dict[str, Any]) -> str:
        """Generate deterministic cache key.

        Args:
            source_data: Input data to generate cache key for

        Returns:
            SHA256 hash of the source data
        """
        data_str = json.dumps(source_data, sort_keys=True)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def create_metadata(self, source_data: dict[str, Any], builder_type: str) -> IRMetadata:
        """Create standard metadata.

        Args:
            source_data: Input data
            builder_type: Type of IR builder

        Returns:
            IRMetadata instance
        """
        return IRMetadata(
            version=1,
            generated_at=datetime.now().isoformat(),
            source_files=len(source_data) if isinstance(source_data, dict) else 1,
            builder_type=builder_type,
        )

    def validate_ir(self, ir_data: IRData) -> bool:
        """Basic IR validation.

        Args:
            ir_data: IR data to validate

        Returns:
            True if valid, False otherwise
        """
        # Basic validation - can be overridden by subclasses
        if not ir_data.metadata:
            return False
        if not ir_data.data:
            return False
        return True
