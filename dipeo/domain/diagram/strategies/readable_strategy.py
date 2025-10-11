"""Readable YAML strategy - forwarding module.

This module provides backward compatibility by re-exporting the refactored
ReadableYamlStrategy from the readable package.

The implementation has been refactored into modular components:
- readable/parser.py: Node and connection parsing
- readable/transformer.py: Data transformations
- readable/serializer.py: Diagram serialization
- readable/flow_parser.py: Flow parsing logic
- readable/strategy.py: Main orchestrator
"""

from .readable.strategy import ReadableYamlStrategy

__all__ = ["ReadableYamlStrategy"]
