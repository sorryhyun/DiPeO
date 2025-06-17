"""
Error handling middleware for the unified executor system.
"""

import logging
import traceback
from typing import Dict, Any, Optional, Callable, List, Set
from datetime import datetime, timedelta
from collections import defaultdict
from ..types import ExecutorResult, ExecutionContext

logger = logging.getLogger(__name__)


class ErrorHandlingMiddleware:
    """Middleware that provides enhanced error handling and recovery strategies."""
    
    def __init__(
        self,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        error_callback: Optional[Callable[[Dict[str, Any], Exception], None]] = None,
        suppress_errors: bool = False,
        error_rate_threshold: float = 0.5,
        error_rate_window_minutes: int = 5
    ):
        """
        Initialize error handling middleware.
        
        Args:
            max_retries: Maximum number of retries for transient errors
            retry_delay: Delay between retries in seconds
            error_callback: Optional callback for error notifications
            suppress_errors: Whether to suppress and log errors instead of raising
            error_rate_threshold: Threshold for error rate alerts (0.0-1.0)
            error_rate_window_minutes: Time window for error rate calculation
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.error_callback = error_callback
        self.suppress_errors = suppress_errors
        self.error_rate_threshold = error_rate_threshold
        self.error_rate_window_minutes = error_rate_window_minutes
        
        # Error tracking
        self._error_counts: Dict[str, int] = defaultdict(int)
        self._error_history: Dict[str, List[datetime]] = defaultdict(list)
        self._retry_counts: Dict[str, int] = defaultdict(int)
        self._circuit_breakers: Dict[str, datetime] = {}
        
        # Define transient error patterns
        self.transient_errors: Set[str] = {
            "TimeoutError",
            "ConnectionError", 
            "TemporaryFailure",
            "RateLimitError",
            "ServiceUnavailable"
        }
    
    async def pre_execute(self, node: Dict[str, Any], context: ExecutionContext) -> None:
        """Check circuit breaker status before execution."""
        node_type = node.get("type", "unknown")
        node_id = node.get("id", "unknown")
        
        # Check if circuit breaker is open for this node type
        if node_type in self._circuit_breakers:
            reset_time = self._circuit_breakers[node_type]
            if datetime.now() < reset_time:
                time_left = (reset_time - datetime.now()).total_seconds()
                raise RuntimeError(
                    f"Circuit breaker open for {node_type}. "
                    f"Too many errors detected. Retry in {time_left:.1f} seconds."
                )
            else:
                # Circuit breaker period expired, remove it
                del self._circuit_breakers[node_type]
                logger.info(f"Circuit breaker reset for {node_type}")
        
        # Clean up old error history
        self._cleanup_error_history(node_type)
    
    async def post_execute(
        self, 
        node: Dict[str, Any], 
        context: ExecutionContext, 
        result: ExecutorResult
    ) -> None:
        """Handle errors and implement recovery strategies."""
        node_type = node.get("type", "unknown")
        node_id = node.get("id", "unknown")
        
        if result.error:
            # Record error
            self._error_counts[node_type] += 1
            self._error_history[node_type].append(datetime.now())
            
            # Log detailed error information
            self._log_error(node, result)
            
            # Check error rate and potentially open circuit breaker
            error_rate = self._calculate_error_rate(node_type)
            if error_rate > self.error_rate_threshold:
                self._open_circuit_breaker(node_type)
            
            # Determine if error is transient
            error_type = result.metadata.get("error_type", "")
            is_transient = any(transient in error_type for transient in self.transient_errors)
            
            # Handle retry logic for transient errors
            if is_transient and self._should_retry(node_id):
                self._retry_counts[node_id] += 1
                logger.warning(
                    f"Transient error detected for {node_type} node {node_id}. "
                    f"Retry {self._retry_counts[node_id]}/{self.max_retries}"
                )
                # Note: Actual retry would be handled by the execution engine
                result.metadata["should_retry"] = True
                result.metadata["retry_count"] = self._retry_counts[node_id]
                result.metadata["retry_delay"] = self.retry_delay
            else:
                # Clean up retry count for non-retryable errors
                if node_id in self._retry_counts:
                    del self._retry_counts[node_id]
            
            # Call error callback if provided
            if self.error_callback:
                try:
                    error_info = {
                        "node_id": node_id,
                        "node_type": node_type,
                        "error": result.error,
                        "error_type": error_type,
                        "timestamp": datetime.now().isoformat()
                    }
                    self.error_callback(error_info, Exception(result.error))
                except Exception as e:
                    logger.error(f"Error callback failed: {e}")
            
            # Suppress error if configured
            if self.suppress_errors:
                logger.error(f"Suppressing error for {node_type} node {node_id}: {result.error}")
                result.error = None
                result.output = {"error_suppressed": True, "original_error": result.error}
        else:
            # Success - clean up retry count
            if node_id in self._retry_counts:
                del self._retry_counts[node_id]
    
    def _should_retry(self, node_id: str) -> bool:
        """Check if node should be retried."""
        return self._retry_counts.get(node_id, 0) < self.max_retries
    
    def _calculate_error_rate(self, node_type: str) -> float:
        """Calculate error rate for a node type within the time window."""
        if node_type not in self._error_history:
            return 0.0
        
        cutoff_time = datetime.now() - timedelta(minutes=self.error_rate_window_minutes)
        recent_errors = [
            error_time for error_time in self._error_history[node_type]
            if error_time > cutoff_time
        ]
        
        # Estimate total executions (this is a simplified approach)
        # In production, you'd track both successes and failures
        total_executions = max(len(recent_errors) * 2, 1)  # Assume 50% error rate minimum
        
        return len(recent_errors) / total_executions
    
    def _open_circuit_breaker(self, node_type: str) -> None:
        """Open circuit breaker for a node type."""
        # Set circuit breaker to open for 30 seconds
        reset_time = datetime.now() + timedelta(seconds=30)
        self._circuit_breakers[node_type] = reset_time
        
        logger.error(
            f"Circuit breaker opened for {node_type}. "
            f"High error rate detected. Will reset at {reset_time.isoformat()}"
        )
    
    def _cleanup_error_history(self, node_type: str) -> None:
        """Remove old entries from error history."""
        if node_type not in self._error_history:
            return
        
        cutoff_time = datetime.now() - timedelta(minutes=self.error_rate_window_minutes * 2)
        self._error_history[node_type] = [
            error_time for error_time in self._error_history[node_type]
            if error_time > cutoff_time
        ]
    
    def _log_error(self, node: Dict[str, Any], result: ExecutorResult) -> None:
        """Log detailed error information."""
        node_type = node.get("type", "unknown")
        node_id = node.get("id", "unknown")
        
        error_details = {
            "node_id": node_id,
            "node_type": node_type,
            "error": result.error,
            "error_type": result.metadata.get("error_type", "Unknown"),
            "validation_errors": result.validation_errors,
            "execution_time": result.execution_time,
            "timestamp": datetime.now().isoformat()
        }
        
        # Add stack trace if available
        if self.suppress_errors:
            error_details["stack_trace"] = traceback.format_exc()
        
        logger.error(
            f"Execution error in {node_type} node",
            extra={"error_details": error_details}
        )
    
    def get_error_stats(self) -> Dict[str, Any]:
        """Get current error statistics."""
        stats = {
            "total_errors": sum(self._error_counts.values()),
            "errors_by_type": dict(self._error_counts),
            "active_circuit_breakers": {
                node_type: reset_time.isoformat()
                for node_type, reset_time in self._circuit_breakers.items()
                if datetime.now() < reset_time
            },
            "retry_counts": dict(self._retry_counts)
        }
        
        # Calculate error rates
        error_rates = {}
        for node_type in self._error_history:
            error_rates[node_type] = self._calculate_error_rate(node_type)
        stats["error_rates"] = error_rates
        
        return stats
    
    def reset_error_stats(self, node_type: Optional[str] = None) -> None:
        """Reset error statistics."""
        if node_type:
            self._error_counts.pop(node_type, None)
            self._error_history.pop(node_type, None)
            self._circuit_breakers.pop(node_type, None)
        else:
            self._error_counts.clear()
            self._error_history.clear()
            self._retry_counts.clear()
            self._circuit_breakers.clear()