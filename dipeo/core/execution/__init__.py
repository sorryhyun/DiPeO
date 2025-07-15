"""Core execution tracking and output management for DiPeO.

This module provides:
- Type-safe node output protocols and implementations
- Execution tracking that separates runtime state from history
- Support for iterative execution without losing state
"""

from dipeo.core.execution.execution_tracker import (
    CompletionStatus,
    ExecutionTracker,
    FlowStatus,
    NodeExecutionRecord,
    NodeRuntimeState,
)
from dipeo.core.execution.node_output import (
    BaseNodeOutput,
    ConditionOutput,
    ConversationOutput,
    DataOutput,
    ErrorOutput,
    NodeOutputProtocol,
    TextOutput,
    serialize_protocol,
    deserialize_protocol,
)

__all__ = [
    # Node outputs
    "NodeOutputProtocol",
    "BaseNodeOutput",
    "TextOutput",
    "ConversationOutput",
    "ConditionOutput",
    "DataOutput",
    "ErrorOutput",
    "serialize_protocol",
    "deserialize_protocol",
    # Execution tracking
    "ExecutionTracker",
    "FlowStatus",
    "CompletionStatus",
    "NodeExecutionRecord",
    "NodeRuntimeState",
]