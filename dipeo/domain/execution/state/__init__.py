"""Domain execution state management."""

from .ports import (
    ExecutionCachePort,
    ExecutionStateRepository,
    ExecutionStateService,
)
from .unified_state_tracker import (
    NodeExecutionRecord,
    NodeRuntimeState,
    NodeState,
    UnifiedStateTracker,
)

# Backward compatibility: StateTracker is now an alias for UnifiedStateTracker
StateTracker = UnifiedStateTracker

# Backward compatibility: ExecutionTracker is now an alias for UnifiedStateTracker
# Note: Old code calling tracker.get_tracker() will still work
ExecutionTracker = UnifiedStateTracker

__all__ = [
    "ExecutionCachePort",
    "ExecutionStateRepository",
    "ExecutionStateService",
    "ExecutionTracker",
    "NodeExecutionRecord",
    "NodeRuntimeState",
    "NodeState",
    "StateTracker",
    "UnifiedStateTracker",
]
