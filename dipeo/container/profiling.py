"""Container initialization profiling utilities."""

import asyncio
import time
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ProfileResult:
    """Result of a profiling operation."""
    name: str
    duration_ms: float
    children: List['ProfileResult'] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def total_duration_ms(self) -> float:
        """Get total duration including children."""
        return self.duration_ms + sum(child.total_duration_ms() for child in self.children)

    def print_tree(self, indent: int = 0) -> None:
        """Print profiling results as a tree."""
        prefix = "  " * indent
        print(f"{prefix}{self.name}: {self.duration_ms:.2f}ms")
        for child in sorted(self.children, key=lambda x: x.duration_ms, reverse=True):
            child.print_tree(indent + 1)


class ContainerProfiler:
    """Profile container initialization."""
    
    def __init__(self):
        self._stack: List[ProfileResult] = []
        self._root: Optional[ProfileResult] = None

    @contextmanager
    def profile(self, name: str, **metadata):
        """Profile a synchronous operation."""
        start_time = time.perf_counter()
        result = ProfileResult(name=name, duration_ms=0, metadata=metadata)
        
        if self._stack:
            self._stack[-1].children.append(result)
        else:
            self._root = result
            
        self._stack.append(result)
        
        try:
            yield result
        finally:
            result.duration_ms = (time.perf_counter() - start_time) * 1000
            self._stack.pop()

    @asynccontextmanager
    async def profile_async(self, name: str, **metadata):
        """Profile an asynchronous operation."""
        start_time = time.perf_counter()
        result = ProfileResult(name=name, duration_ms=0, metadata=metadata)
        
        if self._stack:
            self._stack[-1].children.append(result)
        else:
            self._root = result
            
        self._stack.append(result)
        
        try:
            yield result
        finally:
            result.duration_ms = (time.perf_counter() - start_time) * 1000
            self._stack.pop()

    def get_results(self) -> Optional[ProfileResult]:
        """Get profiling results."""
        return self._root

    def print_results(self) -> None:
        """Print profiling results."""
        if self._root:
            print("\n=== Container Initialization Profile ===")
            self._root.print_tree()
            print(f"\nTotal time: {self._root.total_duration_ms():.2f}ms\n")
        else:
            print("No profiling results available")


# Global profiler instance
_profiler: Optional[ContainerProfiler] = None


def get_profiler() -> Optional[ContainerProfiler]:
    """Get the global profiler instance."""
    return _profiler


def set_profiler(profiler: Optional[ContainerProfiler]) -> None:
    """Set the global profiler instance."""
    global _profiler
    _profiler = profiler


@contextmanager
def enable_profiling():
    """Enable profiling for the duration of the context."""
    profiler = ContainerProfiler()
    set_profiler(profiler)
    try:
        yield profiler
    finally:
        set_profiler(None)
