"""Execution flow controller to manage diagram execution state and flow."""

from typing import Optional, Any, Set, Dict, List, Tuple
from collections import deque
import logging
import json
from datetime import datetime

log = logging.getLogger(__name__)


class ExecutionFlowController:
    """Manages the execution flow state and provides helper methods for execution control."""
    
    def __init__(self, execution_view: Any, enable_visualization: bool = False):
        self.execution_view = execution_view
        self.ready_queue: deque = deque()
        self.executed_nodes: Set[str] = set()
        self.iteration_count: int = 0
        self.enable_visualization = enable_visualization
        
        # Flow visualization data
        self.flow_history: List[Dict[str, Any]] = []
        self.node_states: Dict[str, str] = {}
        self.execution_timeline: List[Tuple[datetime, str, str]] = []
        
    def has_endpoint_executed(self) -> bool:
        """Check if any endpoint node has been executed."""
        for node_view in self.execution_view.node_views.values():
            if node_view.node.type == "endpoint" and node_view.output is not None:
                log.info(f"Endpoint node {node_view.id} executed")
                return True
        return False
    
    def should_skip_node_execution(self, node_view: Any) -> bool:
        """Determine if a node should be skipped due to max iterations."""
        if node_view.node.type not in ["job", "person_job", "loop"]:
            return False
            
        max_iter = node_view.data.get("max_iteration", 1)
        return node_view.exec_count >= max_iter
    
    def get_iterative_nodes(self) -> list[Any]:
        """Get all nodes that support iteration and haven't reached their limit."""
        iterative_nodes = []
        
        for node_view in self.execution_view.node_views.values():
            if node_view.node.type in ["job", "person_job", "loop"]:
                max_iter = node_view.data.get("max_iteration", 1)
                if node_view.exec_count < max_iter and node_view.output is None:
                    iterative_nodes.append(node_view)
                    
        return iterative_nodes
    
    def get_executable_successors(self, node_view: Any, can_execute_fn) -> list[Any]:
        """Get all successor nodes that are ready to execute."""
        successors = []
        
        for edge in node_view.outgoing_edges:
            target = edge.target_view
            
            # Skip if already in queue
            if target in self.ready_queue:
                continue
                
            # Check if it's an iterative node that can still execute
            if target.node.type in ["job", "person_job", "loop"]:
                max_iter = target.data.get("max_iteration", 1)
                if target.exec_count < max_iter and target.output is None:
                    if can_execute_fn(target):
                        successors.append(target)
                        
            # Check if it's a resettable condition node
            elif (target.node.type == "condition" and 
                  target.data.get("condition_type") == "detect_max_iterations"):
                target.output = None  # Reset condition node
                if can_execute_fn(target):
                    successors.append(target)
                    
            # Regular nodes
            elif target.output is None and can_execute_fn(target):
                successors.append(target)
                
        return successors
    
    def get_final_batch_nodes(self, can_execute_fn) -> list[Any]:
        """Get nodes for final execution batch (non-iterative nodes that haven't executed)."""
        final_batch = []
        
        for node_view in self.execution_view.node_views.values():
            if (node_view.output is None and 
                node_view.node.type not in ["job", "person_job", "loop"] and
                can_execute_fn(node_view)):
                final_batch.append(node_view)
                
        return final_batch
    
    def add_to_queue(self, nodes: list[Any]) -> None:
        """Add nodes to the execution queue."""
        for node in nodes:
            if node not in self.ready_queue:
                self.ready_queue.append(node)
    
    def get_next_batch(self) -> list[Any]:
        """Get the next batch of nodes to execute from the queue."""
        batch = []
        batch_size = len(self.ready_queue)
        
        for _ in range(batch_size):
            if self.ready_queue:
                batch.append(self.ready_queue.popleft())
                
        return batch
    
    def increment_iteration(self) -> None:
        """Increment the iteration counter."""
        self.iteration_count += 1
    
    def should_continue_iterations(self, max_iterations: int) -> bool:
        """Check if iterations should continue."""
        return (
            len(self.ready_queue) > 0 and 
            self.iteration_count < max_iterations and 
            not self.has_endpoint_executed()
        )
    
    def record_node_execution(self, node_id: str, status: str, details: Optional[Dict] = None) -> None:
        """Record node execution for visualization."""
        if not self.enable_visualization:
            return
            
        timestamp = datetime.now()
        self.execution_timeline.append((timestamp, node_id, status))
        
        event = {
            "timestamp": timestamp.isoformat(),
            "iteration": self.iteration_count,
            "node_id": node_id,
            "status": status,
            "queue_size": len(self.ready_queue),
            "details": details or {}
        }
        self.flow_history.append(event)
        self.node_states[node_id] = status
    
    def get_flow_visualization(self) -> Dict[str, Any]:
        """Generate execution flow visualization data."""
        if not self.enable_visualization:
            return {"error": "Visualization not enabled"}
            
        # Calculate execution statistics
        total_nodes = len(self.execution_view.node_views)
        executed_count = len(self.executed_nodes)
        
        # Group timeline by iteration
        iterations_data = {}
        for event in self.flow_history:
            iteration = event["iteration"]
            if iteration not in iterations_data:
                iterations_data[iteration] = []
            iterations_data[iteration].append(event)
        
        # Create node execution summary
        node_summary = {}
        for node_id, node_view in self.execution_view.node_views.items():
            node_summary[node_id] = {
                "type": node_view.node.type,
                "exec_count": node_view.exec_count,
                "max_iteration": node_view.data.get("max_iteration", 1),
                "status": self.node_states.get(node_id, "pending"),
                "has_output": node_view.output is not None
            }
        
        return {
            "summary": {
                "total_nodes": total_nodes,
                "executed_nodes": executed_count,
                "total_iterations": self.iteration_count,
                "execution_complete": self.has_endpoint_executed() or executed_count == total_nodes
            },
            "iterations": iterations_data,
            "node_states": node_summary,
            "timeline": [
                {
                    "time": t.isoformat(),
                    "node": node_id,
                    "status": status
                }
                for t, node_id, status in self.execution_timeline
            ]
        }
    
    def log_flow_state(self, message: str) -> None:
        """Log the current flow state for debugging."""
        if log.isEnabledFor(logging.DEBUG):
            queue_nodes = [node.id for node in list(self.ready_queue)]
            log.debug(
                f"{message} - Iteration: {self.iteration_count}, "
                f"Queue: {queue_nodes}, Executed: {len(self.executed_nodes)}"
            )