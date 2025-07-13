"""
Enhanced stateful execution that leverages static typing from the diagram compiler.

This version uses the strongly-typed node classes for better type safety and 
more efficient execution logic.
"""

from typing import Dict, Any, Optional, List, Set, cast
from datetime import datetime

from dipeo.models import (
    NodeID, ExecutionState, NodeState, NodeOutput, NodeExecutionStatus,
    ExecutionStatus, TokenUsage, ExecutionID, DiagramID, NodeType
)
from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.core.static.generated_nodes import (
    PersonJobNode, ConditionNode, StartNode, EndpointNode,
    CodeJobNode, ApiJobNode, DBNode, HookNode
)


class TypedStatefulExecution:
    """Type-aware stateful execution that leverages strongly-typed nodes."""
    
    def __init__(
        self,
        diagram: ExecutableDiagram,
        execution_state: ExecutionState,
        max_global_iterations: int = 100,
    ):
        """Initialize with a typed executable diagram."""
        self.diagram = diagram
        self.state = execution_state
        
        # Global iteration tracking
        self.iteration_count: int = 0
        self.max_global_iterations: int = max_global_iterations
        
        # Cache for ready nodes
        self._ready_nodes_cache: Optional[List[ExecutableNode]] = None
        
        # Track current node and execution history
        self._current_node: Optional[NodeID] = None
        self._executed_nodes: List[str] = []
        self._exec_counts: Dict[str, int] = {}
        
        # Build typed node index for fast lookup
        self._typed_nodes: Dict[NodeID, ExecutableNode] = {
            node.id: node for node in diagram.nodes
        }
        
        # Initialize all nodes to pending if not already set
        self._initialize_node_states()
    
    def _initialize_node_states(self) -> None:
        """Initialize all nodes to PENDING state if not already set."""
        for node in self.diagram.nodes:
            if node.id not in self.state.node_states:
                node_state = NodeState(
                    status=NodeExecutionStatus.PENDING,
                    node_id=node.id
                )
                # Initialize extra fields
                setattr(node_state, "exec_count", 0)
                setattr(node_state, "max_iterations", 1)
                setattr(node_state, "node_type", str(node.type))
                self.state.node_states[str(node.id)] = node_state
    
    def get_typed_node(self, node_id: NodeID) -> Optional[ExecutableNode]:
        """Get a strongly-typed node by ID."""
        return self._typed_nodes.get(node_id)
    
    def get_ready_nodes(self) -> List[ExecutableNode]:
        """Get all nodes that are ready to execute using type-aware logic."""
        if self._ready_nodes_cache is not None:
            return self._ready_nodes_cache
        
        ready = []
        for node in self.diagram.nodes:
            if self._is_node_ready_typed(node):
                ready.append(node)
        
        self._ready_nodes_cache = ready
        return ready
    
    def _is_node_ready_typed(self, node: ExecutableNode) -> bool:
        """Type-aware node readiness check."""
        state = self.get_node_state(node.id)
        if state.status != NodeExecutionStatus.PENDING:
            return False
        
        # Type-specific readiness checks
        if isinstance(node, StartNode):
            # Start nodes are always ready
            return True
        
        # Get incoming edges
        incoming_edges = self.diagram.get_incoming_edges(node.id)
        if not incoming_edges:
            # Nodes without dependencies are ready
            return True
        
        # PersonJobNode specific logic
        if isinstance(node, PersonJobNode):
            exec_count = self.get_node_execution_count(node.id)
            
            # Use the typed max_iteration property directly
            if exec_count >= node.max_iteration:
                return False
            
            if exec_count == 0:
                # First execution - only check 'first' input edges
                first_edges = [e for e in incoming_edges if e.target_input == "first"]
                if first_edges:
                    incoming_edges = first_edges
            else:
                # Subsequent executions - check non-'first' edges
                non_first_edges = [e for e in incoming_edges if e.target_input != "first"]
                incoming_edges = non_first_edges
        
        # Check if all dependencies are satisfied
        for edge in incoming_edges:
            source_node = self.get_typed_node(edge.source_node_id)
            if not source_node:
                continue
            
            # Check if dependency is complete
            dep_state = self.get_node_state(edge.source_node_id)
            if dep_state.status != NodeExecutionStatus.COMPLETED:
                return False
            
            # Type-specific dependency checks
            if isinstance(source_node, ConditionNode):
                if not self._is_conditional_edge_active_typed(edge, source_node):
                    return False
        
        return True
    
    def _is_conditional_edge_active_typed(self, edge, condition_node: ConditionNode) -> bool:
        """Type-aware conditional edge evaluation."""
        # Get the condition result
        condition_value = self.get_node_output(condition_node.id)
        if condition_value is None:
            return False
        
        # Use edge metadata to determine branch
        edge_metadata = edge.metadata or {}
        is_true_branch = edge_metadata.get("branch") == "true"
        is_false_branch = edge_metadata.get("branch") == "false"
        
        # Also check source_output for backward compatibility
        if not is_true_branch and not is_false_branch and edge.source_output:
            is_true_branch = edge.source_output == "true"
            is_false_branch = edge.source_output == "false"
        
        if is_true_branch and condition_value:
            return True
        if is_false_branch and not condition_value:
            return True
        
        # Default to active if no specific branch is indicated
        return not (is_true_branch or is_false_branch)
    
    def should_continue_person_job(self, node_id: NodeID) -> bool:
        """Check if a PersonJobNode should continue iterating."""
        node = self.get_typed_node(node_id)
        if not isinstance(node, PersonJobNode):
            return False
        
        exec_count = self.get_node_execution_count(node_id)
        # Use the typed property directly
        return exec_count < node.max_iteration
    
    def get_person_job_prompt(self, node_id: NodeID) -> Optional[str]:
        """Get the appropriate prompt for a PersonJobNode based on execution count."""
        node = self.get_typed_node(node_id)
        if not isinstance(node, PersonJobNode):
            return None
        
        exec_count = self.get_node_execution_count(node_id)
        
        # Use typed properties directly
        if exec_count == 0 and node.first_only_prompt:
            return node.first_only_prompt
        else:
            return node.default_prompt
    
    def get_endpoint_save_config(self, node_id: NodeID) -> Optional[Dict[str, Any]]:
        """Get save configuration for an EndpointNode."""
        node = self.get_typed_node(node_id)
        if not isinstance(node, EndpointNode):
            return None
        
        # Use typed properties directly
        if node.save_to_file:
            return {
                "save": True,
                "filename": node.file_name or f"output_{node_id}.json"
            }
        return None
    
    def get_code_job_config(self, node_id: NodeID) -> Optional[Dict[str, Any]]:
        """Get execution configuration for a CodeJobNode."""
        node = self.get_typed_node(node_id)
        if not isinstance(node, CodeJobNode):
            return None
        
        # Use typed properties directly
        return {
            "language": node.language.value if hasattr(node.language, 'value') else node.language,
            "code": node.code,
            "timeout": node.timeout
        }
    
    def is_complete(self) -> bool:
        """Check if the execution is complete using type-aware logic."""
        # Get typed end nodes
        end_nodes = [
            node for node in self.diagram.nodes 
            if isinstance(node, EndpointNode)
        ]
        
        if end_nodes:
            # All endpoints must be complete
            all_ends_complete = all(
                self.get_node_state(node.id).status == NodeExecutionStatus.COMPLETED
                for node in end_nodes
            )
            if all_ends_complete:
                return True
        
        # Check if there are any pending or running reachable nodes
        has_pending_reachable = False
        for node in self.diagram.nodes:
            state = self.get_node_state(node.id)
            if state.status in (NodeExecutionStatus.PENDING, NodeExecutionStatus.RUNNING):
                # Special handling for PersonJobNodes that exceeded iterations
                if isinstance(node, PersonJobNode):
                    if self.get_node_execution_count(node.id) >= node.max_iteration:
                        continue
                
                if self._is_node_reachable_typed(node):
                    has_pending_reachable = True
        
        return not has_pending_reachable
    
    def _is_node_reachable_typed(self, node: ExecutableNode) -> bool:
        """Type-aware node reachability check."""
        # Start nodes are always reachable
        if isinstance(node, StartNode):
            return True
        
        visited: Set[NodeID] = set()
        queue: List[NodeID] = []
        
        # Start from completed or running nodes
        for check_node in self.diagram.nodes:
            state = self.get_node_state(check_node.id)
            if state.status in (NodeExecutionStatus.COMPLETED, NodeExecutionStatus.RUNNING):
                # Don't start from endpoints
                if not isinstance(check_node, EndpointNode):
                    queue.append(check_node.id)
        
        # BFS to check reachability
        while queue:
            current_id = queue.pop(0)
            if current_id in visited:
                continue
            
            visited.add(current_id)
            
            if current_id == node.id:
                return True
            
            current_node = self.get_typed_node(current_id)
            if current_node:
                for next_node in self.diagram.get_next_nodes(current_id):
                    # Type-specific reachability logic
                    if isinstance(current_node, ConditionNode):
                        edge = next(
                            (e for e in self.diagram.get_outgoing_edges(current_id)
                             if e.target_node_id == next_node.id),
                            None
                        )
                        if edge and not self._is_conditional_edge_active_typed(edge, current_node):
                            continue
                    
                    if next_node.id not in visited:
                        queue.append(next_node.id)
        
        return False
    
    # Include all the base methods from StatefulExecution for compatibility
    def get_node_state(self, node_id: NodeID) -> NodeState:
        """Get the execution state of a specific node."""
        return self.state.node_states.get(str(node_id), NodeState(
            status=NodeExecutionStatus.PENDING,
            node_id=node_id
        ))
    
    def set_node_state(self, node_id: NodeID, status: NodeExecutionStatus, error: Optional[str] = None) -> None:
        """Set the execution state of a node."""
        node_state = self.state.node_states.get(str(node_id), NodeState(
            status=status,
            node_id=node_id
        ))
        node_state.status = status
        if error:
            node_state.error = error
        if status == NodeExecutionStatus.RUNNING:
            node_state.started_at = datetime.now().isoformat()
        elif status in (NodeExecutionStatus.COMPLETED, NodeExecutionStatus.FAILED):
            node_state.ended_at = datetime.now().isoformat()
        
        self.state.node_states[str(node_id)] = node_state
        self.invalidate_cache()
    
    def set_node_output(self, node_id: NodeID, output: Any) -> None:
        """Store the output of a node execution."""
        self.state.node_outputs[str(node_id)] = NodeOutput(
            node_id=node_id,
            value=output,
            metadata={"timestamp": datetime.now().isoformat()}
        )
        
        # Also update the node state with output
        node_state = self.get_node_state(node_id)
        node_state.output = self.state.node_outputs[str(node_id)]
        self.state.node_states[str(node_id)] = node_state
    
    def get_node_output(self, node_id: NodeID) -> Any:
        """Get the output of a specific node."""
        output = self.state.node_outputs.get(str(node_id))
        if output:
            return output.value
        
        # Check in node state as well
        node_state = self.get_node_state(node_id)
        if node_state and node_state.output:
            return node_state.output.value
        return None
    
    def get_variable(self, key: str) -> Any:
        """Get a variable from the global context."""
        return self.state.variables.get(key)
    
    def set_variable(self, key: str, value: Any) -> None:
        """Set a variable in the global context."""
        self.state.variables[key] = value
    
    def update_variables(self, updates: Dict[str, Any]) -> None:
        """Update multiple variables in the global context."""
        self.state.variables.update(updates)
    
    def invalidate_cache(self) -> None:
        """Invalidate the ready nodes cache."""
        self._ready_nodes_cache = None
    
    def mark_node_running(self, node_id: NodeID) -> None:
        """Mark a node as running and set as current."""
        self.set_node_state(node_id, NodeExecutionStatus.RUNNING)
        self._current_node = node_id
        
        # Update execution count
        node_id_str = str(node_id)
        self._exec_counts[node_id_str] = self._exec_counts.get(node_id_str, 0) + 1
    
    def mark_node_complete(self, node_id: NodeID) -> None:
        """Mark a node as completed."""
        self.set_node_state(node_id, NodeExecutionStatus.COMPLETED)
        
        # Add to executed nodes list
        node_id_str = str(node_id)
        if node_id_str not in self._executed_nodes:
            self._executed_nodes.append(node_id_str)
    
    def mark_node_failed(self, node_id: NodeID, error: str) -> None:
        """Mark a node as failed with error."""
        self.set_node_state(node_id, NodeExecutionStatus.FAILED, error)
    
    def get_completed_nodes(self) -> List[NodeID]:
        """Get list of all completed node IDs."""
        completed = []
        for node_id, state in self.state.node_states.items():
            if state.status == NodeExecutionStatus.COMPLETED:
                completed.append(NodeID(node_id))
        return completed
    
    def get_progress(self) -> Dict[str, Any]:
        """Get execution progress statistics."""
        total_nodes = len(self.diagram.nodes)
        completed = sum(
            1 for state in self.state.node_states.values()
            if state.status == NodeExecutionStatus.COMPLETED
        )
        failed = sum(
            1 for state in self.state.node_states.values()
            if state.status == NodeExecutionStatus.FAILED
        )
        running = sum(
            1 for state in self.state.node_states.values()
            if state.status == NodeExecutionStatus.RUNNING
        )
        
        return {
            "total_nodes": total_nodes,
            "completed_nodes": completed,
            "failed_nodes": failed,
            "running_nodes": running,
            "progress_percentage": completed / total_nodes if total_nodes > 0 else 0
        }
    
    def get_node_execution_count(self, node_id: NodeID) -> int:
        """Get the execution count for a specific node."""
        # Check node state extra fields
        node_state = self.get_node_state(node_id)
        if node_state:
            return getattr(node_state, "exec_count", 0)
        
        # Fall back to internal tracking
        return self._exec_counts.get(str(node_id), 0)
    
    
    # Properties for compatibility
    @property
    def current_node_id(self) -> str:
        """Get the ID of the currently executing node."""
        return str(self._current_node) if self._current_node else ""
    
    @property
    def executed_nodes(self) -> List[str]:
        """Get the list of node IDs that have been executed."""
        return self._executed_nodes
    
    @property
    def diagram_id(self) -> str:
        """Get the current diagram ID."""
        return str(self.state.diagram_id) if self.state.diagram_id else ""
    
    @property
    def execution_id(self) -> str:
        """Get the execution ID."""
        return str(self.state.id)
    
    
    def increment_iteration(self) -> None:
        """Increment global iteration counter."""
        self.iteration_count += 1
    
    def should_continue(self) -> bool:
        """Check if execution should continue based on completion and iteration limit."""
        if self.iteration_count >= self.max_global_iterations:
            return False
        
        # Use typed execution's is_complete method
        return not self.is_complete()
    
