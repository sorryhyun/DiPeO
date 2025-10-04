"""Configuration management for Strawberry IR builder."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import yaml

from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)


class StrawberryConfig:
    """Manages configuration for Strawberry GraphQL code generation."""

    def __init__(self, root: Path):
        """Initialize configuration from root path.

        Args:
            root: Root path containing configuration YAML files
        """
        self.root = root
        self.type_mappings = self._load("type_mappings.yaml")
        self.domain_fields = self._load("domain_fields.yaml")
        self.schema = self._opt("schema_config.yaml")

    def _load(self, name: str) -> dict[str, Any]:
        """Load required configuration file.

        Args:
            name: Configuration file name

        Returns:
            Configuration data as dictionary

        Raises:
            FileNotFoundError: If required config file is missing
        """
        config_path = self.root / name
        try:
            with open(config_path) as f:
                data = yaml.safe_load(f) or {}
                # logger.debug(f"Loaded configuration from {name}: {len(data)} items")
                return data
        except FileNotFoundError:
            # logger.error(f"Required configuration file not found: {config_path}")
            raise

    def _opt(self, name: str) -> dict[str, Any]:
        """Load optional configuration file.

        Args:
            name: Configuration file name

        Returns:
            Configuration data if file exists, empty dict otherwise
        """
        config_path = self.root / name
        if config_path.exists():
            return self._load(name)
        # logger.debug(f"Optional configuration file not found: {name}, using defaults")
        return {}

    def to_dict(self) -> dict[str, Any]:
        """Convert configuration to dictionary for serialization.

        Returns:
            Configuration data as dictionary
        """
        return {
            "type_mappings": self.type_mappings,
            "domain_fields": self.domain_fields,
            "schema": self.schema,
        }
