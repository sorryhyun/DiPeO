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
            dur_ms: Duration in milliseconds (will be rounded to integer)
            **metadata: Additional context (model, token_count, etc.)
        """
        # Round to integer milliseconds (show 0 for sub-millisecond operations)
        dur_ms_int = round(dur_ms)

        with self._data_lock:
            if phase in self._data[exec_id][node_id]:
                # Accumulate if phase runs multiple times
                self._data[exec_id][node_id][phase] += dur_ms_int
                # Track count of occurrences
                count_key = f"{phase}__count"
                self._data[exec_id][node_id][count_key] = (
                    self._data[exec_id][node_id].get(count_key, 1) + 1
                )
                # Track maximum individual duration
                max_key = f"{phase}__max"
                self._data[exec_id][node_id][max_key] = max(
                    self._data[exec_id][node_id].get(max_key, 0), dur_ms_int
                )
            else:
                self._data[exec_id][node_id][phase] = dur_ms_int
                # Initialize count
                count_key = f"{phase}__count"
                self._data[exec_id][node_id][count_key] = 1
                # Initialize max with first value
                max_key = f"{phase}__max"
                self._data[exec_id][node_id][max_key] = dur_ms_int

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
