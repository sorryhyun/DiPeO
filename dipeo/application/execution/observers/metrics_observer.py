"""Metrics collection observer for execution analysis and optimization."""

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from dipeo.core.bak.events import EventConsumer, EventEmitter, EventType, ExecutionEvent

logger = logging.getLogger(__name__)


@dataclass
class NodeMetrics:
    """Metrics for a single node execution."""
    node_id: str
    node_type: str
    start_time: float
    end_time: Optional[float] = None
    duration_ms: Optional[float] = None
    memory_usage: Optional[int] = None
    token_usage: Optional[Dict[str, int]] = None
    error: Optional[str] = None
    dependencies: Set[str] = field(default_factory=set)


@dataclass
class ExecutionMetrics:
    """Aggregated metrics for an entire execution."""
    execution_id: str
    start_time: float
    end_time: Optional[float] = None
    total_duration_ms: Optional[float] = None
    node_metrics: Dict[str, NodeMetrics] = field(default_factory=dict)
    critical_path: List[str] = field(default_factory=list)
    parallelizable_groups: List[List[str]] = field(default_factory=list)
    bottlenecks: List[str] = field(default_factory=list)


@dataclass
class DiagramOptimization:
    """Optimization suggestions for a diagram."""
    execution_id: str
    diagram_id: Optional[str]
    bottlenecks: List[Dict[str, Any]]
    parallelizable: List[List[str]]
    suggested_changes: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "execution_id": self.execution_id,
            "diagram_id": self.diagram_id,
            "bottlenecks": self.bottlenecks,
            "parallelizable": self.parallelizable,
            "suggested_changes": self.suggested_changes,
        }


class MetricsObserver(EventConsumer):
    """Collects execution metrics for analysis and optimization suggestions.
    
    This observer:
    - Tracks execution performance metrics
    - Identifies bottlenecks and optimization opportunities
    - Emits suggestions for diagram improvements
    - Provides foundation for self-modifying diagrams
    """
    
    def __init__(self, event_bus: Optional[EventEmitter] = None):
        self._metrics_buffer: Dict[str, ExecutionMetrics] = {}
        self._node_dependencies: Dict[str, Dict[str, Set[str]]] = {}  # exec_id -> node_id -> deps
        self.event_bus = event_bus
        self._analysis_threshold_ms = 1000  # Nodes taking > 1s are potential bottlenecks
        self._cleanup_task: Optional[asyncio.Task] = None
        self._running = False
    
    async def start(self) -> None:
        """Start the metrics observer."""
        if self._running:
            return
        
        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.debug("MetricsObserver started")
    
    async def stop(self) -> None:
        """Stop the metrics observer."""
        self._running = False
        
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass
        
        logger.info("MetricsObserver stopped")
    
    async def consume(self, event: ExecutionEvent) -> None:
        """Process execution events to collect metrics."""
        try:
            if event.type == EventType.EXECUTION_STARTED:
                await self._handle_execution_started(event)
            elif event.type == EventType.NODE_STARTED:
                await self._handle_node_started(event)
            elif event.type == EventType.NODE_COMPLETED:
                await self._handle_node_completed(event)
            elif event.type == EventType.NODE_FAILED:
                await self._handle_node_failed(event)
            elif event.type == EventType.EXECUTION_COMPLETED:
                await self._handle_execution_completed(event)
        except Exception as e:
            logger.error(f"Error processing event: {e}", exc_info=True)
    
    async def _handle_execution_started(self, event: ExecutionEvent) -> None:
        """Initialize metrics for a new execution."""
        self._metrics_buffer[event.execution_id] = ExecutionMetrics(
            execution_id=event.execution_id,
            start_time=event.timestamp,
        )
        self._node_dependencies[event.execution_id] = {}
    
    async def _handle_node_started(self, event: ExecutionEvent) -> None:
        """Track node start time."""
        metrics = self._metrics_buffer.get(event.execution_id)
        if not metrics:
            return
        
        node_id = event.data.get("node_id")
        if not node_id:
            return
        
        metrics.node_metrics[node_id] = NodeMetrics(
            node_id=node_id,
            node_type=event.data.get("node_type", "unknown"),
            start_time=event.timestamp,
        )
        
        # Track dependencies
        deps = event.data.get("dependencies", [])
        if deps:
            self._node_dependencies[event.execution_id][node_id] = set(deps)
    
    async def _handle_node_completed(self, event: ExecutionEvent) -> None:
        """Track node completion and collect metrics."""
        metrics = self._metrics_buffer.get(event.execution_id)
        if not metrics:
            return
        
        node_id = event.data.get("node_id")
        if not node_id or node_id not in metrics.node_metrics:
            return
        
        node_metrics = metrics.node_metrics[node_id]
        node_metrics.end_time = event.timestamp
        node_metrics.duration_ms = (node_metrics.end_time - node_metrics.start_time) * 1000
        
        # Collect additional metrics
        event_metrics = event.data.get("metrics", {})
        node_metrics.memory_usage = event_metrics.get("memory_usage")
        node_metrics.token_usage = event_metrics.get("token_usage")
    
    async def _handle_node_failed(self, event: ExecutionEvent) -> None:
        """Track node failure."""
        metrics = self._metrics_buffer.get(event.execution_id)
        if not metrics:
            return
        
        node_id = event.data.get("node_id")
        if not node_id or node_id not in metrics.node_metrics:
            return
        
        node_metrics = metrics.node_metrics[node_id]
        node_metrics.end_time = event.timestamp
        node_metrics.duration_ms = (node_metrics.end_time - node_metrics.start_time) * 1000
        node_metrics.error = event.data.get("error", "Unknown error")
    
    async def _handle_execution_completed(self, event: ExecutionEvent) -> None:
        """Analyze execution and emit optimization suggestions."""
        metrics = self._metrics_buffer.get(event.execution_id)
        if not metrics:
            return
        
        metrics.end_time = event.timestamp
        metrics.total_duration_ms = (metrics.end_time - metrics.start_time) * 1000
        
        # Analyze execution patterns
        await self._analyze_execution(event.execution_id)
        
        # Clean up
        del self._metrics_buffer[event.execution_id]
        if event.execution_id in self._node_dependencies:
            del self._node_dependencies[event.execution_id]
    
    async def _analyze_execution(self, execution_id: str) -> None:
        """Analyze execution metrics and emit optimization suggestions."""
        metrics = self._metrics_buffer.get(execution_id)
        if not metrics:
            return
        
        # Identify patterns
        bottlenecks = self._find_bottlenecks(metrics)
        parallelizable = self._find_parallelizable_nodes(metrics)
        critical_path = self._find_critical_path(metrics)
        
        # Store patterns in metrics
        metrics.bottlenecks = [b["node_id"] for b in bottlenecks]
        metrics.parallelizable_groups = parallelizable
        metrics.critical_path = critical_path
        
        # Emit metrics collected event for persistence
        if self.event_bus:
            # Convert metrics to dict for serialization
            metrics_dict = {
                "execution_id": metrics.execution_id,
                "start_time": metrics.start_time,
                "end_time": metrics.end_time,
                "total_duration_ms": metrics.total_duration_ms,
                "critical_path": metrics.critical_path,
                "parallelizable_groups": metrics.parallelizable_groups,
                "bottlenecks": metrics.bottlenecks,
                "node_metrics": {
                    node_id: {
                        "node_id": nm.node_id,
                        "node_type": nm.node_type,
                        "start_time": nm.start_time,
                        "end_time": nm.end_time,
                        "duration_ms": nm.duration_ms,
                        "memory_usage": nm.memory_usage,
                        "token_usage": nm.token_usage,
                        "error": nm.error,
                        "dependencies": list(nm.dependencies),
                    }
                    for node_id, nm in metrics.node_metrics.items()
                }
            }
            
            await self.event_bus.emit(ExecutionEvent(
                type=EventType.METRICS_COLLECTED,
                execution_id=execution_id,
                timestamp=time.time(),
                data={"metrics": metrics_dict}
            ))
        
        if bottlenecks or parallelizable:
            optimization = DiagramOptimization(
                execution_id=execution_id,
                diagram_id=None,  # Would need to track this
                bottlenecks=bottlenecks,
                parallelizable=parallelizable,
            )
            
            # Generate specific suggestions
            if bottlenecks:
                optimization.suggested_changes.append({
                    "type": "optimize_bottlenecks",
                    "description": f"Optimize {len(bottlenecks)} slow nodes",
                    "nodes": [b["node_id"] for b in bottlenecks],
                })
            
            if parallelizable:
                optimization.suggested_changes.append({
                    "type": "enable_parallelization",
                    "description": f"Run {len(parallelizable)} node groups in parallel",
                    "groups": parallelizable,
                })
            
            # Emit optimization event
            if self.event_bus:
                await self.event_bus.emit(ExecutionEvent(
                    type=EventType.OPTIMIZATION_SUGGESTED,
                    execution_id=execution_id,
                    timestamp=time.time(),
                    data={"optimization": optimization.to_dict()}
                ))
    
    def _find_bottlenecks(self, metrics: ExecutionMetrics) -> List[Dict[str, Any]]:
        """Identify nodes that are performance bottlenecks."""
        bottlenecks = []
        
        for node_id, node_metrics in metrics.node_metrics.items():
            if node_metrics.duration_ms and node_metrics.duration_ms > self._analysis_threshold_ms:
                bottlenecks.append({
                    "node_id": node_id,
                    "node_type": node_metrics.node_type,
                    "duration_ms": node_metrics.duration_ms,
                    "percentage": (node_metrics.duration_ms / metrics.total_duration_ms * 100)
                    if metrics.total_duration_ms else 0,
                })
        
        # Sort by duration
        bottlenecks.sort(key=lambda x: x["duration_ms"], reverse=True)
        
        return bottlenecks
    
    def _find_parallelizable_nodes(
        self, metrics: ExecutionMetrics
    ) -> List[List[str]]:
        """Find groups of nodes that could run in parallel."""
        execution_id = metrics.execution_id
        if execution_id not in self._node_dependencies:
            return []
        
        deps = self._node_dependencies[execution_id]
        parallelizable_groups = []
        
        # Find nodes with no dependencies on each other
        nodes = list(metrics.node_metrics.keys())
        
        for i, node1 in enumerate(nodes):
            group = [node1]
            
            for j, node2 in enumerate(nodes[i+1:], i+1):
                # Check if nodes can run in parallel
                node1_deps = deps.get(node1, set())
                node2_deps = deps.get(node2, set())
                
                # Nodes can run in parallel if neither depends on the other
                if node2 not in node1_deps and node1 not in node2_deps:
                    # Also check transitive dependencies
                    if not self._has_dependency_path(deps, node1, node2) and \
                       not self._has_dependency_path(deps, node2, node1):
                        group.append(node2)
            
            if len(group) > 1:
                parallelizable_groups.append(group)
        
        # Deduplicate groups
        unique_groups = []
        seen = set()
        for group in parallelizable_groups:
            group_key = tuple(sorted(group))
            if group_key not in seen:
                seen.add(group_key)
                unique_groups.append(group)
        
        return unique_groups
    
    def _has_dependency_path(
        self, deps: Dict[str, Set[str]], from_node: str, to_node: str
    ) -> bool:
        """Check if there's a dependency path from one node to another."""
        visited = set()
        queue = [from_node]
        
        while queue:
            current = queue.pop(0)
            if current == to_node:
                return True
            
            if current in visited:
                continue
            
            visited.add(current)
            queue.extend(deps.get(current, set()))
        
        return False
    
    def _find_critical_path(self, metrics: ExecutionMetrics) -> List[str]:
        """Find the critical path through the execution."""
        # Simple implementation: nodes that took the longest and were sequential
        # A more sophisticated version would use graph analysis
        
        sorted_nodes = sorted(
            metrics.node_metrics.items(),
            key=lambda x: x[1].duration_ms or 0,
            reverse=True
        )
        
        # Return top nodes as a simple critical path
        return [node_id for node_id, _ in sorted_nodes[:5]]
    
    async def _cleanup_loop(self) -> None:
        """Periodically clean up old metrics."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Run every 5 minutes
                
                # Clean up metrics older than 1 hour
                current_time = time.time()
                cutoff_time = current_time - 3600
                
                to_remove = [
                    exec_id for exec_id, metrics in self._metrics_buffer.items()
                    if metrics.start_time < cutoff_time
                ]
                
                for exec_id in to_remove:
                    del self._metrics_buffer[exec_id]
                    if exec_id in self._node_dependencies:
                        del self._node_dependencies[exec_id]
                
                if to_remove:
                    logger.info(f"Cleaned up metrics for {len(to_remove)} old executions")
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup loop: {e}", exc_info=True)