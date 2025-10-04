from collections import defaultdict
from threading import Lock
from typing import Any


class TimingCollector:
    """In-process singleton for collecting timing metrics.

    Thread-safe collector keyed by exec_id. No file I/O, no parsing.
    """

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._data = defaultdict(lambda: defaultdict(dict))
                    cls._instance._data_lock = Lock()
        return cls._instance

    def record(
        self, exec_id: str, node_id: str, phase: str, dur_ms: float, **metadata: Any
    ) -> None:
        """Record timing for a specific phase.

        Args:
            exec_id: Execution ID
            node_id: Node ID (use "system" for non-node phases)
            phase: Phase name (e.g., "input_extraction", "llm_completion")
            dur_ms: Duration in milliseconds
            **metadata: Additional context (model, token_count, etc.)
        """
        with self._data_lock:
            if phase in self._data[exec_id][node_id]:
                # Accumulate if phase runs multiple times
                self._data[exec_id][node_id][phase] += dur_ms
            else:
                self._data[exec_id][node_id][phase] = dur_ms

            # Store metadata separately if provided
            if metadata:
                meta_key = f"{phase}_metadata"
                self._data[exec_id][node_id][meta_key] = metadata

    def get(self, exec_id: str) -> dict[str, dict[str, float]]:
        """Get all timing data for an execution (non-destructive)."""
        with self._data_lock:
            return dict(self._data.get(exec_id, {}))

    def pop(self, exec_id: str) -> dict[str, dict[str, float]]:
        """Get and remove timing data for an execution."""
        with self._data_lock:
            return dict(self._data.pop(exec_id, {}))

    def clear(self, exec_id: str | None = None) -> None:
        """Clear data for specific exec_id or all data."""
        with self._data_lock:
            if exec_id:
                self._data.pop(exec_id, None)
            else:
                self._data.clear()


# Global singleton instance
timing_collector = TimingCollector()
