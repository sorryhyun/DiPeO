"""Preprocess phase for Claude Code translation.

This phase handles session-level processing and preparation including:
- Session event pruning and filtering
- Field pruning and cleanup
- Metadata extraction
- Session orchestration
"""

from .base import (
    BaseSessionProcessor,
    SessionChange,
    SessionChangeType,
    SessionProcessingReport,
)
from .config import (
    PreprocessConfig,
    SessionEventPrunerConfig,
    SessionFieldPrunerConfig,
)
from .session_event_pruner import SessionEventPruner
from .session_field_pruner import SessionFieldPruner
from .session_orchestrator import SessionOrchestrator

__all__ = [
    # Base classes
    "BaseSessionProcessor",
    # Configuration
    "PreprocessConfig",
    "SessionChange",
    "SessionChangeType",
    # Processors
    "SessionEventPruner",
    "SessionEventPrunerConfig",
    "SessionFieldPruner",
    "SessionFieldPrunerConfig",
    "SessionOrchestrator",
    "SessionProcessingReport",
]
