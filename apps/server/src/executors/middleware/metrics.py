"""
Metrics middleware for the unified executor system.
"""

import time
import logging
from typing import Dict, Any, Optional, List
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from ..types import ExecutorResult, ExecutionContext

logger = logging.getLogger(__name__)


@dataclass
class NodeMetrics:
    """Metrics for a single node type."""
    execution_count: int = 0
    success_count: int = 0
    error_count: int = 0
    total_execution_time: float = 0.0
    min_execution_time: Optional[float] = None
    max_execution_time: Optional[float] = None
    avg_execution_time: float = 0.0
    total_tokens_used: int = 0
    errors: List[str] = field(default_factory=list)
    last_execution: Optional[datetime] = None


class MetricsMiddleware:
    """Middleware that collects and tracks execution metrics."""
    
    def __init__(self, enable_detailed_metrics: bool = True):
        """
        Initialize metrics middleware.
        
        Args:
            enable_detailed_metrics: Whether to collect detailed metrics (default: True)
        """
        self.enable_detailed_metrics = enable_detailed_metrics
        self._metrics: Dict[str, NodeMetrics] = defaultdict(NodeMetrics)
        self._global_metrics = NodeMetrics()
        self._active_executions: Dict[str, float] = {}
    
    async def pre_execute(self, node: Dict[str, Any], context: ExecutionContext) -> None:
        """Record metrics before node execution."""
        if not self.enable_detailed_metrics:
            return
        
        node_id = node.get("id", "unknown")
        node_type = node.get("type", "unknown")
        
        # Track active execution start time
        self._active_executions[node_id] = time.time()
        
        # Increment execution count
        self._metrics[node_type].execution_count += 1
        self._global_metrics.execution_count += 1
    
    async def post_execute(
        self, 
        node: Dict[str, Any], 
        context: ExecutionContext, 
        result: ExecutorResult
    ) -> None:
        """Record metrics after node execution."""
        node_id = node.get("id", "unknown")
        node_type = node.get("type", "unknown")
        
        # Calculate execution time
        start_time = self._active_executions.pop(node_id, None)
        if start_time:
            execution_time = time.time() - start_time
        else:
            execution_time = result.execution_time or 0.0
        
        metrics = self._metrics[node_type]
        
        # Update success/error counts
        if result.error:
            metrics.error_count += 1
            self._global_metrics.error_count += 1
            
            # Track error types
            if self.enable_detailed_metrics:
                error_msg = f"{type(result.error).__name__ if hasattr(result.error, '__name__') else 'Error'}: {str(result.error)[:100]}"
                metrics.errors.append(error_msg)
                # Keep only last 10 errors per node type
                metrics.errors = metrics.errors[-10:]
        else:
            metrics.success_count += 1
            self._global_metrics.success_count += 1
        
        # Update execution times
        metrics.total_execution_time += execution_time
        self._global_metrics.total_execution_time += execution_time
        
        if metrics.min_execution_time is None or execution_time < metrics.min_execution_time:
            metrics.min_execution_time = execution_time
        if metrics.max_execution_time is None or execution_time > metrics.max_execution_time:
            metrics.max_execution_time = execution_time
        
        # Calculate average
        if metrics.execution_count > 0:
            metrics.avg_execution_time = metrics.total_execution_time / metrics.execution_count
        
        # Update token usage
        if result.token_usage:
            total_tokens = result.token_usage.get("total_tokens", 0)
            metrics.total_tokens_used += total_tokens
            self._global_metrics.total_tokens_used += total_tokens
        
        # Update last execution time
        metrics.last_execution = datetime.now()
        
        # Log summary periodically (every 100 executions)
        if self._global_metrics.execution_count % 100 == 0:
            self._log_metrics_summary()
    
    def get_metrics(self, node_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get metrics for a specific node type or all metrics.
        
        Args:
            node_type: Specific node type to get metrics for (None for all)
            
        Returns:
            Dictionary containing metrics
        """
        if node_type:
            metrics = self._metrics.get(node_type)
            if metrics:
                return self._metrics_to_dict(metrics)
            return {}
        
        # Return all metrics
        return {
            "global": self._metrics_to_dict(self._global_metrics),
            "by_node_type": {
                node_type: self._metrics_to_dict(metrics)
                for node_type, metrics in self._metrics.items()
            }
        }
    
    def reset_metrics(self, node_type: Optional[str] = None) -> None:
        """
        Reset metrics for a specific node type or all metrics.
        
        Args:
            node_type: Specific node type to reset (None for all)
        """
        if node_type:
            if node_type in self._metrics:
                self._metrics[node_type] = NodeMetrics()
        else:
            self._metrics.clear()
            self._global_metrics = NodeMetrics()
            self._active_executions.clear()
    
    def _metrics_to_dict(self, metrics: NodeMetrics) -> Dict[str, Any]:
        """Convert NodeMetrics to dictionary."""
        return {
            "execution_count": metrics.execution_count,
            "success_count": metrics.success_count,
            "error_count": metrics.error_count,
            "success_rate": metrics.success_count / metrics.execution_count if metrics.execution_count > 0 else 0.0,
            "total_execution_time": metrics.total_execution_time,
            "min_execution_time": metrics.min_execution_time,
            "max_execution_time": metrics.max_execution_time,
            "avg_execution_time": metrics.avg_execution_time,
            "total_tokens_used": metrics.total_tokens_used,
            "recent_errors": metrics.errors[-5:] if self.enable_detailed_metrics else [],
            "last_execution": metrics.last_execution.isoformat() if metrics.last_execution else None
        }
    
    def _log_metrics_summary(self) -> None:
        """Log a summary of current metrics."""
        global_metrics = self._metrics_to_dict(self._global_metrics)
        
        logger.info(
            f"Metrics Summary - Total executions: {global_metrics['execution_count']}, "
            f"Success rate: {global_metrics['success_rate']:.2%}, "
            f"Avg time: {global_metrics['avg_execution_time']:.3f}s, "
            f"Total tokens: {global_metrics['total_tokens_used']}"
        )
        
        # Log top 3 most used node types
        sorted_types = sorted(
            self._metrics.items(), 
            key=lambda x: x[1].execution_count, 
            reverse=True
        )[:3]
        
        for node_type, metrics in sorted_types:
            metrics_dict = self._metrics_to_dict(metrics)
            logger.info(
                f"  {node_type}: {metrics.execution_count} executions, "
                f"{metrics_dict['success_rate']:.2%} success rate, "
                f"avg {metrics.avg_execution_time:.3f}s"
            )