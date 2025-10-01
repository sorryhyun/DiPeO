"""Build context and configuration management for IR builders."""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import yaml

from dipeo.infrastructure.codegen.ir_builders.type_system_unified import UnifiedTypeConverter


@dataclass
class BuildContext:
    """Context for IR build operations with shared state and configuration.

    Provides centralized access to:
    - Configuration management
    - Type conversion utilities
    - Build metadata
    - Cached resources
    """

    config_path: Optional[Path] = None
    config: dict[str, Any] = field(default_factory=dict)
    _type_converter: Optional[UnifiedTypeConverter] = None
    _base_dir: Optional[Path] = None
    _cache: dict[str, Any] = field(default_factory=dict)
    _step_results: dict[str, Any] = field(default_factory=dict)
    _metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize build context."""
        if self.config_path:
            self.config = self._load_config()
        if not self._base_dir:
            self._base_dir = self._resolve_base_dir()

    def _resolve_base_dir(self) -> Path:
        """Resolve the base directory for the project.

        Returns:
            Path to the project root directory
        """
        base_dir = os.environ.get("DIPEO_BASE_DIR")
        if base_dir:
            return Path(base_dir)

        # Try to find project root by looking for characteristic files
        current = Path.cwd()
        for _ in range(10):  # Limit search depth
            if (current / "pyproject.toml").exists() or (current / "Makefile").exists():
                return current
            if current.parent == current:
                break
            current = current.parent

        return Path.cwd()

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

    @property
    def type_converter(self) -> UnifiedTypeConverter:
        """Get or create the type converter instance.

        Returns:
            Shared UnifiedTypeConverter instance
        """
        if self._type_converter is None:
            custom_mappings = self.config.get("type_mappings")
            self._type_converter = UnifiedTypeConverter(custom_mappings=custom_mappings) if custom_mappings else UnifiedTypeConverter()
        return self._type_converter

    @property
    def base_dir(self) -> Path:
        """Get the base directory for the project.

        Returns:
            Path to the project root
        """
        return self._base_dir

    def get_cache_key(self, source_data: Any) -> str:
        """Generate deterministic cache key for data.

        Args:
            source_data: Input data to generate cache key for

        Returns:
            SHA256 hash of the source data
        """
        if isinstance(source_data, dict | list):
            data_str = json.dumps(source_data, sort_keys=True)
        else:
            data_str = str(source_data)
        return hashlib.sha256(data_str.encode()).hexdigest()

    def cache_get(self, key: str) -> Optional[Any]:
        """Get cached value by key.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        return self._cache.get(key)

    def cache_set(self, key: str, value: Any) -> None:
        """Set cached value.

        Args:
            key: Cache key
            value: Value to cache
        """
        self._cache[key] = value

    def cache_compute(self, key: str, compute_fn: callable) -> Any:
        """Get cached value or compute and cache it.

        Args:
            key: Cache key
            compute_fn: Function to compute value if not cached

        Returns:
            Cached or computed value
        """
        if key in self._cache:
            return self._cache[key]
        value = compute_fn()
        self._cache[key] = value
        return value

    def create_metadata(self, source_info: dict[str, Any]) -> dict[str, Any]:
        """Create standard metadata for IR output.

        Args:
            source_info: Information about the source data

        Returns:
            Metadata dictionary
        """
        return {
            "version": 1,
            "generated_at": datetime.now().isoformat(),
            "source_info": source_info,
            "config_hash": self.get_cache_key(self.config) if self.config else None,
        }

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-separated key.

        Args:
            key: Configuration key (e.g., "strawberry.skip_validation")
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        parts = key.split(".")
        value = self.config
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
                if value is None:
                    return default
            else:
                return default
        return value

    def update_config(self, updates: dict[str, Any]) -> None:
        """Update configuration with new values.

        Args:
            updates: Dictionary of configuration updates
        """
        self.config.update(updates)
        # Clear type converter cache when config changes
        self._type_converter = None

    def get_step_data(self, step_name: str, default: Any = None) -> Any:
        """Get data from a previously executed step.

        Args:
            step_name: Name of the step
            default: Default value if step hasn't been executed

        Returns:
            Step's output data or default if step hasn't been executed
        """
        return self._step_results.get(step_name, default)

    def set_step_data(self, step_name: str, data: Any) -> None:
        """Store data from a step execution.

        Args:
            step_name: Name of the step
            data: Step's output data
        """
        self._step_results[step_name] = data

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """Get metadata value by key.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default if not found
        """
        return self._metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """Store metadata value.

        Args:
            key: Metadata key
            value: Metadata value to store
        """
        self._metadata[key] = value

    def update_metadata(self, metadata: dict[str, Any]) -> None:
        """Update metadata with new values.

        Args:
            metadata: Dictionary of metadata updates
        """
        self._metadata.update(metadata)
