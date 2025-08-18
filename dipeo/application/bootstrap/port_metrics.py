"""Port usage metrics collection for Wave 5 migration monitoring."""

import functools
import logging
import time
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Dict, List, Optional

logger = logging.getLogger(__name__)


@dataclass
class PortMetrics:
    """Metrics for port usage tracking."""
    
    call_count: int = 0
    error_count: int = 0
    total_duration: float = 0.0
    last_call_time: Optional[datetime] = None
    error_types: Dict[str, int] = field(default_factory=lambda: defaultdict(int))
    
    @property
    def average_duration(self) -> float:
        """Calculate average call duration."""
        return self.total_duration / self.call_count if self.call_count > 0 else 0.0
    
    @property
    def error_rate(self) -> float:
        """Calculate error rate as percentage."""
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
            self._metrics: Dict[str, Dict[str, PortMetrics]] = defaultdict(
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
        error: Optional[Exception] = None
    ) -> None:
        """Record a port method call.
        
        Args:
            port_name: Name of the port (e.g., "StateStore", "LLMService")
            method_name: Method that was called
            duration: Call duration in seconds
            is_v2: Whether this was a V2 port call
            error: Exception if the call failed
        """
        metrics = self._metrics[port_name][method_name]
        metrics.call_count += 1
        metrics.total_duration += duration
        metrics.last_call_time = datetime.now()
        
        if error:
            metrics.error_count += 1
            error_type = type(error).__name__
            metrics.error_types[error_type] += 1
        
        # Track V1 vs V2 usage
        if is_v2:
            self._v2_calls += 1
        else:
            self._v1_calls += 1
        
        # Log high-level metrics periodically
        total_calls = self._v1_calls + self._v2_calls
        if total_calls % 100 == 0:
            self._log_summary()
    
    def get_metrics(self, port_name: Optional[str] = None) -> Dict[str, Any]:
        """Get metrics for a specific port or all ports.
        
        Args:
            port_name: Optional port name to filter by
            
        Returns:
            Dictionary of metrics
        """
        if port_name:
            return {
                method: {
                    "call_count": metrics.call_count,
                    "error_count": metrics.error_count,
                    "error_rate": metrics.error_rate,
                    "avg_duration": metrics.average_duration,
                    "last_call": metrics.last_call_time.isoformat() if metrics.last_call_time else None,
                    "error_types": dict(metrics.error_types),
                }
                for method, metrics in self._metrics[port_name].items()
            }
        
        return {
            "v1_calls": self._v1_calls,
            "v2_calls": self._v2_calls,
            "v2_percentage": (self._v2_calls / (self._v1_calls + self._v2_calls) * 100) if (self._v1_calls + self._v2_calls) > 0 else 0,
            "ports": {
                port: self.get_metrics(port)
                for port in self._metrics.keys()
            }
        }
    
    def _log_summary(self) -> None:
        """Log a summary of metrics."""
        total = self._v1_calls + self._v2_calls
        v2_pct = (self._v2_calls / total * 100) if total > 0 else 0
        
        logger.info(
            f"📊 Port Usage: V1={self._v1_calls} V2={self._v2_calls} "
            f"({v2_pct:.1f}% on V2)"
        )
        
        # Log top errors
        all_errors = defaultdict(int)
        for port_metrics in self._metrics.values():
            for method_metrics in port_metrics.values():
                for error_type, count in method_metrics.error_types.items():
                    all_errors[error_type] += count
        
        if all_errors:
            top_errors = sorted(all_errors.items(), key=lambda x: x[1], reverse=True)[:3]
            logger.warning(
                f"⚠️  Top errors: {', '.join(f'{err}={cnt}' for err, cnt in top_errors)}"
            )
    
    def reset(self) -> None:
        """Reset all metrics."""
        self._metrics.clear()
        self._v1_calls = 0
        self._v2_calls = 0


# Global collector instance
_collector = PortMetricsCollector()


def track_port_call(port_name: str, is_v2: bool = False):
    """Decorator to track port method calls.
    
    Args:
        port_name: Name of the port being tracked
        is_v2: Whether this is a V2 domain port
        
    Example:
        @track_port_call("StateStore", is_v2=True)
        async def get_state(self, execution_id: str):
            ...
    """
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
                    error=error
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
                    error=error
                )
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper
    
    return decorator


def get_port_metrics(port_name: Optional[str] = None) -> Dict[str, Any]:
    """Get current port usage metrics.
    
    Args:
        port_name: Optional port name to filter by
        
    Returns:
        Dictionary of metrics
    """
    return _collector.get_metrics(port_name)


def reset_port_metrics() -> None:
    """Reset all port metrics."""
    _collector.reset()


# Utility function to add metrics to existing ports
def add_metrics_to_port(port_instance: Any, port_name: str, is_v2: bool = False) -> Any:
    """Dynamically add metrics tracking to a port instance.
    
    Args:
        port_instance: The port instance to wrap
        port_name: Name of the port
        is_v2: Whether this is a V2 port
        
    Returns:
        Wrapped port instance with metrics
    """
    class MetricsWrapper:
        def __init__(self, wrapped):
            self._wrapped = wrapped
        
        def __getattr__(self, name):
            attr = getattr(self._wrapped, name)
            
            # If it's a callable method, wrap it with metrics
            if callable(attr) and not name.startswith("_"):
                return track_port_call(port_name, is_v2)(attr)
            
            return attr
    
    return MetricsWrapper(port_instance)