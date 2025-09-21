"""Convert phase for Claude Code translation.

This phase transforms processed sessions into DiPeO diagram structures including:
- Node building from conversation turns and tool events
- Connection creation between nodes
- Light format diagram assembly
"""

from .connection_builder import ConnectionBuilder
from .converter import Converter
from .diagram_assembler import DiagramAssembler

# Export refactored NodeBuilder as the main NodeBuilder
from .node_builder_refactored import NodeBuilder
from .payload_processor import PayloadProcessor

# Also export new components for direct access if needed
from .person_registry import PersonRegistry
from .position_manager import GridPositionManager, PositionManager

__all__ = [
    "ConnectionBuilder",
    "Converter",
    "DiagramAssembler",
    "GridPositionManager",
    "NodeBuilder",
    "PayloadProcessor",
    "PersonRegistry",
    "PositionManager",
]
