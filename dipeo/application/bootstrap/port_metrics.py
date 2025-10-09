"""Port usage metrics collection for Wave 5 migration monitoring."""

import functools
import logging
import time
from collections import defaultdict
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import datetime
from typing import TYPE_CHECKING, Any

from dipeo.config.base_logger import get_module_logger

if TYPE_CHECKING:
    from dipeo.application.registry import ServiceRegistry

logger = get_module_logger(__name__)


@dataclass
class PortMetrics:
    """Metrics for port usage tracking."""

    call_count: int = 0
    error_count: int = 0
    total_duration: float = 0.0
    last_call_time: datetime | None = None
    error_types: dict[str, int] = field(default_factory=lambda: defaultdict(int))

    @property
    def average_duration(self) -> float:
        return self.total_duration / self.call_count if self.call_count > 0 else 0.0

    @property
    def error_rate(self) -> float:
        return (self.error_count / self.call_count * 100) if self.call_count > 0 else 0.0


class PortMetricsCollector:
    """Singleton collector for port usage metrics."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._metrics: dict[str, dict[str, PortMetrics]] = defaultdict(
                lambda: defaultdict(PortMetrics)
            )
            self._v1_calls = 0
            self._v2_calls = 0
            self._initialized = True

    def record_call(
        self,
        port_name: str,
        method_name: str,
        duration: float,
        is_v2: bool,
        error: Exception | None = None,
    ) -> None:
        """Record a port method call."""
        metrics = self._metrics[port_name][method_name]
        metrics.call_count += 1
        metrics.total_duration += duration
        metrics.last_call_time = datetime.now()

        if error:
            metrics.error_count += 1
            error_type = type(error).__name__
            metrics.error_types[error_type] += 1

        if is_v2:
            self._v2_calls += 1
        else:
            self._v1_calls += 1

        total_calls = self._v1_calls + self._v2_calls
        if total_calls % 100 == 0:
            self._log_summary()

    def get_metrics(self, port_name: str | None = None) -> dict[str, Any]:
        """Get metrics for a specific port or all ports."""
        if port_name:
            return {
                method: {
                    "call_count": metrics.call_count,
                    "error_count": metrics.error_count,
                    "error_rate": metrics.error_rate,
                    "avg_duration": metrics.average_duration,
                    "last_call": metrics.last_call_time.isoformat()
                    if metrics.last_call_time
                    else None,
                    "error_types": dict(metrics.error_types),
                }
                for method, metrics in self._metrics[port_name].items()
            }

        return {
            "v1_calls": self._v1_calls,
            "v2_calls": self._v2_calls,
            "v2_percentage": (self._v2_calls / (self._v1_calls + self._v2_calls) * 100)
            if (self._v1_calls + self._v2_calls) > 0
            else 0,
            "ports": {port: self.get_metrics(port) for port in self._metrics},
        }

    def _log_summary(self) -> None:
        """Log a summary of metrics."""
        total = self._v1_calls + self._v2_calls
        v2_pct = (self._v2_calls / total * 100) if total > 0 else 0

        logger.info(
            f"📊 Port Usage: V1={self._v1_calls} V2={self._v2_calls} " f"({v2_pct:.1f}% on V2)"
        )

        all_errors = defaultdict(int)
        for port_metrics in self._metrics.values():
            for method_metrics in port_metrics.values():
                for error_type, count in method_metrics.error_types.items():
                    all_errors[error_type] += count

        if all_errors:
            top_errors = sorted(all_errors.items(), key=lambda x: x[1], reverse=True)[:3]
            logger.warning(f"⚠️  Top errors: {', '.join(f'{err}={cnt}' for err, cnt in top_errors)}")

    def reset(self) -> None:
        self._metrics.clear()
        self._v1_calls = 0
        self._v2_calls = 0


_collector = PortMetricsCollector()


def track_port_call(port_name: str, is_v2: bool = False):
    """Decorator to track port method calls."""

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.time()
            error = None

            try:
                result = await func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration = time.time() - start_time
                _collector.record_call(
                    port_name=port_name,
                    method_name=func.__name__,
                    duration=duration,
                    is_v2=is_v2,
                    error=error,
                )

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            start_time = time.time()
            error = None

            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                error = e
                raise
            finally:
                duration = time.time() - start_time
                _collector.record_call(
                    port_name=port_name,
                    method_name=func.__name__,
                    duration=duration,
                    is_v2=is_v2,
                    error=error,
                )

        import asyncio

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


def get_port_metrics(port_name: str | None = None) -> dict[str, Any]:
    """Get current port usage metrics."""
    return _collector.get_metrics(port_name)


def reset_port_metrics() -> None:
    _collector.reset()


def add_metrics_to_port(port_instance: Any, port_name: str, is_v2: bool = False) -> Any:
    """Dynamically add metrics tracking to a port instance."""
    import os

    if os.getenv("DIPEO_PORT_METRICS") != "1":
        return port_instance

    class MetricsWrapper:
        def __init__(self, wrapped):
            self._wrapped = wrapped

        def __getattr__(self, name):
            attr = getattr(self._wrapped, name)

            if callable(attr) and not name.startswith("_"):
                return track_port_call(port_name, is_v2)(attr)

            return attr

    return MetricsWrapper(port_instance)


def wire_port_metrics(registry: "ServiceRegistry") -> None:
    """Wire port metrics collection to all registered services."""
    import os

    if os.getenv("DIPEO_PORT_METRICS") != "1":
        logger.debug("Port metrics disabled (set DIPEO_PORT_METRICS=1 to enable)")
        return

    logger.info("🔬 Wiring port metrics collection (development mode)")

    from dipeo.application.registry.keys import (
        API_INVOKER,
        BLOB_STORE,
        DB_OPERATIONS_SERVICE,
        DIAGRAM_COMPILER,
        DIAGRAM_PORT,
        EVENT_BUS,
        FILESYSTEM_ADAPTER,
        INTEGRATED_API_SERVICE,
        LLM_SERVICE,  # LLM_CLIENT removed - no longer needed
        MESSAGE_ROUTER,
        STATE_CACHE,
        STATE_REPOSITORY,
        STATE_SERVICE,
    )

    port_mappings = [
        (STATE_REPOSITORY, "StateRepository", True),
        (STATE_SERVICE, "StateService", True),
        (STATE_CACHE, "StateCache", True),
        (LLM_SERVICE, "LLMService", True),
        # (LLM_CLIENT, "LLMClient", True),  # Removed - no longer needed
        (FILESYSTEM_ADAPTER, "FileSystem", True),
        (BLOB_STORE, "BlobStore", True),
        (MESSAGE_ROUTER, "MessageRouter", True),
        (EVENT_BUS, "EventBus", True),
        (API_INVOKER, "ApiInvoker", True),
        (INTEGRATED_API_SERVICE, "IntegratedApi", False),
        (DB_OPERATIONS_SERVICE, "DBOperations", True),
        (DIAGRAM_PORT, "DiagramPort", True),
        (DIAGRAM_COMPILER, "DiagramCompiler", True),
    ]

    wrapped_count = 0
    for service_key, port_name, is_v2 in port_mappings:
        if registry.has(service_key):
            service = registry.resolve(service_key)
            wrapped = add_metrics_to_port(service, port_name, is_v2)
            registry.unregister(service_key)
            registry.register(service_key, wrapped)
            wrapped_count += 1

    logger.info(f"✅ Wrapped {wrapped_count} services with port metrics")
