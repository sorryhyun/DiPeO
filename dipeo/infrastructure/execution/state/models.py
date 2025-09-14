"""Data models for cache-first state store."""

import time
from dataclasses import dataclass, field
from typing import Any

from dipeo.diagram_generated import ExecutionState, LLMUsage, Status


@dataclass
class CacheEntry:
    """Enhanced cache entry with metadata for cache-first architecture."""

    state: ExecutionState
    node_outputs: dict[str, Any] = field(default_factory=dict)
    node_statuses: dict[str, Status] = field(default_factory=dict)
    node_errors: dict[str, str] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    llm_usage: LLMUsage | None = None

    # Metadata
    last_access_time: float = field(default_factory=time.time)
    last_write_time: float = field(default_factory=time.time)
    access_count: int = 0
    is_dirty: bool = False
    is_persisted: bool = False
    checkpoint_count: int = 0

    def touch(self):
        """Update access time and count."""
        self.last_access_time = time.time()
        self.access_count += 1

    def mark_dirty(self):
        """Mark cache entry as having unpersisted changes."""
        self.is_dirty = True
        self.last_write_time = time.time()


@dataclass
class PersistenceCheckpoint:
    """Checkpoint for periodic persistence."""

    execution_id: str
    checkpoint_time: float
    node_count: int
    is_final: bool = False


@dataclass
class CacheMetrics:
    """Metrics for cache performance tracking."""

    cache_hits: int = 0
    cache_misses: int = 0
    db_reads: int = 0
    db_writes: int = 0
    checkpoints: int = 0
    cache_evictions: int = 0
    warm_cache_hits: int = 0

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate percentage."""
        total = self.cache_hits + self.cache_misses
        return (self.cache_hits / total * 100) if total > 0 else 0

    def to_dict(self) -> dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "db_reads": self.db_reads,
            "db_writes": self.db_writes,
            "checkpoints": self.checkpoints,
            "cache_evictions": self.cache_evictions,
            "warm_cache_hits": self.warm_cache_hits,
            "cache_hit_rate": self.cache_hit_rate,
        }
