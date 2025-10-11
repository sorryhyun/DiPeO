"""Light YAML strategy - forwarding module.

This module provides backward compatibility by re-exporting the refactored
LightYamlStrategy from the light package.

The implementation has been refactored into modular components:
- light/parser.py: Node and configuration parsing
- light/connection_processor.py: Connection and handle processing
- light/serializer.py: Diagram serialization to light format
- light/strategy.py: Main orchestrator
"""

from .light.strategy import LightYamlStrategy

__all__ = ["LightYamlStrategy"]
