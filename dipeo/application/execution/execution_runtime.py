"""
Consolidated execution runtime that merges SimpleExecution and UnifiedExecutionContext.

This refactored implementation provides a single, clear interface for execution management,
removing unnecessary indirection layers and consolidating state management.
"""

import asyncio
import logging
from datetime import datetime
from typing import TYPE_CHECKING, Any, Union

from dipeo.core.dynamic.execution_context import ExecutionContext
from dipeo.core.execution.execution_tracker import ExecutionTracker, FlowStatus, CompletionStatus
from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.core.static.generated_nodes import (
    ConditionNode,
    EndpointNode,
    PersonJobNode,
    StartNode,
)
from dipeo.models import (
    ExecutionState,
    ExecutionStatus,
    NodeExecutionStatus,
    NodeID,
    NodeState,
    TokenUsage,
)

if TYPE_CHECKING:
    from dipeo.application.unified_service_registry import UnifiedServiceRegistry, ServiceKey

logger = logging.getLogger(__name__)


class ExecutionRuntime(ExecutionContext):
    """Unified execution runtime that manages both execution flow and state.
    
    This consolidates the functionality of SimpleExecution and UnifiedExecutionContext
    into a single, cohesive component that:
    - Manages node execution state and transitions
    - Tracks execution counts and outputs
    - Determines node readiness
    - Implements the ExecutionContext protocol
    - Provides clear state management without delegation chains
    
    Execution Count Semantics:
    - Uses 1-based counting: execution count is incremented BEFORE node execution
    - First execution: exec_count = 1
    - Second execution: exec_count = 2, etc.
    - PersonJobNodes should check `exec_count > max_iteration` to execute exactly max_iteration times
    - This design allows first_only_prompt to work with `exec_count == 1`
    """
    
    def __init__(
        self,
        diagram: ExecutableDiagram,
        execution_state: ExecutionState,
        service_registry: "UnifiedServiceRegistry",
    ):
        """Initialize the execution runtime.
        
        Args:
            diagram: The executable diagram to run
            execution_state: Initial execution state (for resumption)
            service_registry: Service registry for dependency injection
        """
        self.diagram = diagram
        self._execution_id = execution_state.id
        self._diagram_id = execution_state.diagram_id
        self._service_registry = service_registry
        
        # Core state tracking - NodeState is still needed for persistence
        self._node_states: dict[NodeID, NodeState] = {}
        self._variables: dict[str, Any] = {}
        
        # Runtime tracking
        self._current_node_id: NodeID | None = None
        
        # Metadata for handlers
        self.metadata: dict[str, Any] = {}
        
        # Thread safety
        self._state_lock = asyncio.Lock()
        
        # New execution tracker for better state management
        self._tracker = ExecutionTracker()
        
        # Initialize from existing state
        self._load_from_state(execution_state)
        
        # Initialize any missing node states
        self._initialize_node_states()
    
    def _load_from_state(self, state: ExecutionState) -> None:
        """Load runtime state from persisted execution state."""
        # Load node states
        if state.node_states:
            for node_id_str, node_state in state.node_states.items():
                self._node_states[NodeID(node_id_str)] = node_state
        
        # Load node outputs into tracker (protocol format only)
        if state.node_outputs:
            for node_id_str, output_data in state.node_outputs.items():
                from dipeo.core.execution.node_output import deserialize_protocol
                node_id = NodeID(node_id_str)
                
                # All outputs should now be in protocol format
                protocol_output = deserialize_protocol(output_data)
                
                # Store in tracker
                self._tracker._last_outputs[node_id] = protocol_output
        
        # Load execution counts into tracker
        if state.exec_counts:
            for node_id_str, count in state.exec_counts.items():
                # Pre-populate tracker counts
                for _ in range(count):
                    self._tracker.start_execution(NodeID(node_id_str))
                    self._tracker.complete_execution(
                        NodeID(node_id_str),
                        CompletionStatus.SUCCESS
                    )
        
        # Load variables
        if state.variables:
            self._variables = state.variables.copy()
        
        # Load executed nodes list into tracker
        if state.executed_nodes:
            # Tracker maintains execution order automatically
            pass
    
    def _initialize_node_states(self) -> None:
        """Initialize states for any nodes not already tracked."""
        for node in self.diagram.nodes:
            if node.id not in self._node_states:
                self._node_states[node.id] = NodeState(
                    status=NodeExecutionStatus.PENDING,
                    node_id=node.id
                )
    
    # ========== Node Readiness and Execution Flow ==========
    
    def get_ready_nodes(self) -> list[ExecutableNode]:
        """Get all nodes that are ready to execute."""
        ready = []
        for node in self.diagram.nodes:
            if self._is_node_ready(node):
                ready.append(node)
        return ready
    
    def _is_node_ready(self, node: ExecutableNode) -> bool:
        """Check if a node is ready to execute."""
        # Not pending? Not ready
        state = self._node_states.get(node.id)
        if not state or state.status != NodeExecutionStatus.PENDING:
            return False
        
        # Start nodes are always ready when pending
        if isinstance(node, StartNode):
            return True
        
        # Check dependencies
        incoming_edges = self.diagram.get_incoming_edges(node.id)

        # Special handling for PersonJobNodes
        if isinstance(node, PersonJobNode):
            exec_count = self._tracker.get_execution_count(node.id)
            
            # Reached max iterations? Not ready
            if exec_count >= node.max_iteration:
                return False
            
            # First execution? Only check 'first' inputs or non-loop edges
            if exec_count == 0:
                first_edges = [e for e in incoming_edges if e.target_input == "first"]
                if first_edges:
                    incoming_edges = first_edges
                else:
                    # No 'first' edges - filter out loop edges from condition nodes
                    non_loop_edges = []
                    for edge in incoming_edges:
                        source_node = self.diagram.get_node(edge.source_node_id)
                        if source_node and not isinstance(source_node, ConditionNode):
                            non_loop_edges.append(edge)
                    if non_loop_edges:
                        incoming_edges = non_loop_edges

        # All dependencies must be completed or max iterations reached
        for edge in incoming_edges:
            dep_state = self._node_states.get(edge.source_node_id)
            if not dep_state:
                return False
            
            # Check if dependency has executed at least once (for looping nodes)
            dep_exec_count = self._tracker.get_execution_count(edge.source_node_id)
            dep_node = self.diagram.get_node(edge.source_node_id)
            
            # For PersonJobNodes that are PENDING but have executed, consider them "complete enough"
            if (isinstance(dep_node, PersonJobNode) and 
                dep_state.status == NodeExecutionStatus.PENDING and 
                dep_exec_count > 0):
                # This is a looping node that has executed at least once
                logger.debug(f"Node {node.id} dependency {edge.source_node_id} is a looping node with {dep_exec_count} executions")
            else:
                # Accept both COMPLETED and MAXITER_REACHED as valid completion states
                if dep_state.status not in (NodeExecutionStatus.COMPLETED, NodeExecutionStatus.MAXITER_REACHED):
                    return False
            
            # For condition nodes, check branch activation
            source_node = self.diagram.get_node(edge.source_node_id)
            if isinstance(source_node, ConditionNode):
                branch_active = self._is_condition_branch_active(source_node.id, edge.source_output)
                if not branch_active:
                    return False
        
        return True
    
    def _is_condition_branch_active(self, condition_node_id: NodeID, branch: str) -> bool:
        """Check if a specific branch of a condition node is active."""
        # Try tracker first for newer output format
        tracker_output = self._tracker.get_last_output(condition_node_id)
        if tracker_output:
            from dipeo.core.execution.node_output import ConditionOutput
            if isinstance(tracker_output, ConditionOutput):
                # Use the proper ConditionOutput methods
                active_branch, _ = tracker_output.get_branch_output()
                return branch == active_branch
            elif hasattr(tracker_output, 'value'):
                # Handle boolean value directly
                if isinstance(tracker_output.value, bool):
                    return (branch == "condtrue" and tracker_output.value) or \
                           (branch == "condfalse" and not tracker_output.value)
        
        # Should not reach here if tracker has output
        return False
    
    def is_complete(self) -> bool:
        """Check if execution is complete."""
        # Any nodes still running?
        for state in self._node_states.values():
            if state.status == NodeExecutionStatus.RUNNING:
                return False
        
        # Any nodes ready to run?
        return len(self.get_ready_nodes()) == 0
    
    # ========== State Transitions ==========
    
    def transition_node_to_running(self, node_id: NodeID) -> None:
        """Transition a node to running state.
        
        This increments execution count and updates state atomically.
        """
        # Use asyncio.run_coroutine_threadsafe for thread safety without changing the interface
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._async_transition_node_to_running(node_id))
        except RuntimeError:
            # No event loop running, execute synchronously (for tests)
            asyncio.run(self._async_transition_node_to_running(node_id))
    
    async def _async_transition_node_to_running(self, node_id: NodeID) -> None:
        """Internal async implementation of transition_node_to_running.
        
        IMPORTANT: Execution counts are 1-based and incremented BEFORE execution:
        - First execution: count goes from 0 -> 1, handler sees exec_count = 1
        - Second execution: count goes from 1 -> 2, handler sees exec_count = 2
        - This allows first_only_prompt to trigger when exec_count == 1
        """
        async with self._state_lock:
            # Use ExecutionTracker to start execution
            execution_number = self._tracker.start_execution(node_id)
            
            # Update state
            state = self._node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.PENDING,
                node_id=node_id
            )
            state.status = NodeExecutionStatus.RUNNING
            state.started_at = datetime.now()
            self._node_states[node_id] = state
            
            # Set current node
            self._current_node_id = node_id

    
    def transition_node_to_completed(self, node_id: NodeID, output: Any = None) -> None:
        """Transition a node to completed state with output."""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._async_transition_node_to_completed(node_id, output))
        except RuntimeError:
            asyncio.run(self._async_transition_node_to_completed(node_id, output))
    
    def update_node_state_without_tracker(self, node_id: NodeID, output: Any = None) -> None:
        """Update node state without calling the tracker (used when tracker already completed)."""
        # Update state
        state = self._node_states.get(node_id) or NodeState(
            status=NodeExecutionStatus.RUNNING,
            node_id=node_id
        )
        state.status = NodeExecutionStatus.COMPLETED
        state.ended_at = datetime.now()
        state.error = None
        self._node_states[node_id] = state
        
        # Output is now stored in tracker only
    
    async def _async_transition_node_to_completed(self, node_id: NodeID, output: Any = None) -> None:
        """Internal async implementation of transition_node_to_completed."""
        async with self._state_lock:
            # Output should already be NodeOutputProtocol from handlers
            node_output_protocol = None
            if output is not None:
                from dipeo.core.execution.node_output import BaseNodeOutput
                if hasattr(output, 'value') and hasattr(output, 'metadata'):
                    # Already a protocol-compliant output
                    node_output_protocol = output
                else:
                    # Wrap raw value (shouldn't happen with proper handlers)
                    node_output_protocol = BaseNodeOutput(
                        value=output,
                        node_id=node_id,
                        metadata={}
                    )
            
            # Use ExecutionTracker to complete execution
            self._tracker.complete_execution(
                node_id=node_id,
                status=CompletionStatus.SUCCESS,
                output=node_output_protocol
            )
            
            # Update state
            state = self._node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.RUNNING,
                node_id=node_id
            )
            state.status = NodeExecutionStatus.COMPLETED
            state.ended_at = datetime.now()
            state.error = None
            self._node_states[node_id] = state
            
            # Output is now stored in tracker only
            
            # Clear current node
            if self._current_node_id == node_id:
                self._current_node_id = None
            
            # Check for downstream resets (loops)
            await self._async_reset_downstream_nodes_if_needed(node_id)
            

    def transition_node_to_failed(self, node_id: NodeID, error: str) -> None:
        """Transition a node to failed state."""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._async_transition_node_to_failed(node_id, error))
        except RuntimeError:
            asyncio.run(self._async_transition_node_to_failed(node_id, error))
    
    async def _async_transition_node_to_failed(self, node_id: NodeID, error: str) -> None:
        """Internal async implementation of transition_node_to_failed."""
        async with self._state_lock:
            # Use ExecutionTracker to complete with failure
            from dipeo.core.execution.node_output import ErrorOutput
            error_output = ErrorOutput(
                value=error,
                node_id=node_id,
                error_type="ExecutionError"
            )
            self._tracker.complete_execution(
                node_id=node_id,
                status=CompletionStatus.FAILED,
                output=error_output,
                error=error
            )
            
            state = self._node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.RUNNING,
                node_id=node_id
            )
            state.status = NodeExecutionStatus.FAILED
            state.ended_at = datetime.now()
            state.error = error
            self._node_states[node_id] = state
            
            # Clear current node
            if self._current_node_id == node_id:
                self._current_node_id = None
            

    def transition_node_to_maxiter(self, node_id: NodeID) -> None:
        """Transition a node to max iterations reached state."""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._async_transition_node_to_maxiter(node_id))
        except RuntimeError:
            asyncio.run(self._async_transition_node_to_maxiter(node_id))
    
    async def _async_transition_node_to_maxiter(self, node_id: NodeID) -> None:
        """Internal async implementation of transition_node_to_maxiter."""
        async with self._state_lock:
            # Mark in tracker as max iterations reached
            from dipeo.core.execution.node_output import BaseNodeOutput
            max_iter_output = BaseNodeOutput(
                value="Maximum iterations reached",
                node_id=node_id,
                metadata={"reason": "max_iterations"}
            )
            self._tracker.complete_execution(
                node_id=node_id,
                status=CompletionStatus.MAX_ITER,
                output=max_iter_output
            )
            
            state = self._node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.PENDING,
                node_id=node_id
            )
            state.status = NodeExecutionStatus.MAXITER_REACHED
            state.ended_at = datetime.now()
            self._node_states[node_id] = state
            

    def transition_node_to_skipped(self, node_id: NodeID) -> None:
        """Transition a node to skipped state."""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._async_transition_node_to_skipped(node_id))
        except RuntimeError:
            asyncio.run(self._async_transition_node_to_skipped(node_id))
    
    async def _async_transition_node_to_skipped(self, node_id: NodeID) -> None:
        """Internal async implementation of transition_node_to_skipped."""
        async with self._state_lock:
            # Mark in tracker as skipped
            from dipeo.core.execution.node_output import BaseNodeOutput
            skipped_output = BaseNodeOutput(
                value="Node skipped",
                node_id=node_id,
                metadata={"reason": "branch_not_taken"}
            )
            self._tracker.complete_execution(
                node_id=node_id,
                status=CompletionStatus.SKIPPED,
                output=skipped_output
            )
            
            state = self._node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.PENDING,
                node_id=node_id
            )
            state.status = NodeExecutionStatus.SKIPPED
            state.ended_at = datetime.now()
            self._node_states[node_id] = state
            

    def reset_node(self, node_id: NodeID) -> None:
        """Reset a node to pending state (for loops)."""
        try:
            loop = asyncio.get_running_loop()
            asyncio.create_task(self._async_reset_node(node_id))
        except RuntimeError:
            asyncio.run(self._async_reset_node(node_id))
    
    async def _async_reset_node(self, node_id: NodeID) -> None:
        """Internal async implementation of reset_node."""
        async with self._state_lock:
            # Use tracker to reset for iteration (preserves execution history)
            self._tracker.reset_for_iteration(node_id)
            
            state = self._node_states.get(node_id) or NodeState(
                status=NodeExecutionStatus.COMPLETED,
                node_id=node_id
            )
            state.status = NodeExecutionStatus.PENDING
            state.started_at = None
            state.ended_at = None
            state.error = None
            self._node_states[node_id] = state
            
            # Don't clear output for PersonJobNodes - we need it for condition checks
            # The output will be overwritten when the node executes again
            node = self.diagram.get_node(node_id)
            if node and not isinstance(node, PersonJobNode):
                # Clear output for non-PersonJobNodes
                # Output is tracked in ExecutionTracker
                pass

    async def _async_reset_downstream_nodes_if_needed(self, node_id: NodeID) -> None:
        """Reset downstream nodes if they're part of a loop (async version)."""
        outgoing_edges = [e for e in self.diagram.edges if e.source_node_id == node_id]
        nodes_to_reset = []
        

        for edge in outgoing_edges:
            target_node = self.diagram.get_node(edge.target_node_id)
            if not target_node:
                continue
            
            # Check if target was already executed
            target_state = self._node_states.get(target_node.id)
            if not target_state or target_state.status != NodeExecutionStatus.COMPLETED:
                continue
            
            # Check if we can reset this node
            can_reset = True
            
            # Don't reset one-time nodes or condition nodes (they control the loop)
            if isinstance(target_node, (StartNode, EndpointNode, ConditionNode)):
                can_reset = False

            # For PersonJobNodes, check max_iteration
            if isinstance(target_node, PersonJobNode):
                exec_count = self._tracker.get_execution_count(target_node.id)
                # Fix: Use > instead of >= to match the fixed PersonJobNode logic
                if exec_count > target_node.max_iteration:
                    can_reset = False

            if can_reset:
                nodes_to_reset.append(target_node.id)

        # Reset nodes and cascade
        for node_id_to_reset in nodes_to_reset:
            await self._async_reset_node(node_id_to_reset)
            await self._async_reset_downstream_nodes_if_needed(node_id_to_reset)
    
    @property
    def service_registry(self) -> "UnifiedServiceRegistry":
        """Get the service registry for dependency injection."""
        return self._service_registry
    
    # ========== ExecutionContext Protocol Implementation ==========
    
    def get_node_state(self, node_id: NodeID) -> NodeState | None:
        """Get the execution state of a node."""
        return self._node_states.get(node_id)
    
    def set_node_state(self, node_id: NodeID, state: NodeState) -> None:
        """Set the execution state of a node."""
        self._node_states[node_id] = state
    
    def get_node_result(self, node_id: NodeID) -> dict[str, Any] | None:
        """Get the execution result of a completed node."""
        # Get from tracker
        protocol_output = self._tracker.get_last_output(node_id)
        if protocol_output:
            result = {"value": protocol_output.value}
            if hasattr(protocol_output, 'metadata') and protocol_output.metadata:
                result["metadata"] = protocol_output.metadata
            return result
        return None
    
    def get_completed_nodes(self) -> list[NodeID]:
        """Get list of all completed node IDs."""
        return [
            node_id for node_id, state in self._node_states.items()
            if state.status == NodeExecutionStatus.COMPLETED
        ]
    
    def get_variable(self, key: str) -> Any:
        """Get a variable from the execution context."""
        return self._variables.get(key)
    
    def get_node_execution_count(self, node_id: NodeID) -> int:
        """Get the execution count for a node."""
        return self._tracker.get_execution_count(node_id)
    
    # ========== Additional Methods ==========
    
    def get_service(self, service_key: Union[str, "ServiceKey"]) -> Any:
        """Get a service from the registry.
        
        Args:
            service_key: Either a string name (legacy) or ServiceKey instance
            
        Returns:
            The requested service or None if not found
        """
        from dipeo.application.unified_service_registry import ServiceKey
        
        if isinstance(service_key, ServiceKey):
            return self._service_registry.get(service_key.name)
        else:
            # Legacy string-based access
            return self._service_registry.get(service_key)
    
    def get_node_output(self, node_id: str) -> Any:
        """Get the output value of a node."""
        protocol_output = self._tracker.get_last_output(NodeID(node_id))
        return protocol_output.value if protocol_output else None
    
    def get_node(self, node_id: NodeID) -> ExecutableNode | None:
        """Get a node by ID from the diagram."""
        return self.diagram.get_node(node_id)
    
    def resolve_inputs(self, node: ExecutableNode) -> dict[str, Any]:
        """Resolve all inputs for a node."""
        from dipeo.application.execution.input.typed_input_resolution import (
            TypedInputResolutionService,
        )
        from dipeo.core.static.generated_nodes import PersonJobNode
        
        # Create typed input resolution service
        typed_input_service = TypedInputResolutionService()
        
        # Get memory config if applicable
        node_memory_config = None
        if isinstance(node, PersonJobNode) and node.memory_config:
            node_memory_config = node.memory_config
        
        # Collect protocol outputs for input resolution
        node_outputs_dict = {}
        for node in self.diagram.nodes:
            protocol_output = self._tracker.get_last_output(node.id)
            if protocol_output:
                # Pass protocol output directly
                node_outputs_dict[str(node.id)] = protocol_output
        
        # Resolve inputs
        return typed_input_service.resolve_inputs_for_node(
            node_id=str(node.id),
            node_type=node.type,
            diagram=self.diagram,
            node_outputs=node_outputs_dict,
            node_exec_counts={str(node_id): self._tracker.get_execution_count(node_id) 
                            for node_id in self._node_states.keys()},
            node_memory_config=node_memory_config
        )
    
    def to_execution_state(self) -> ExecutionState:
        """Convert runtime state to ExecutionState for persistence."""
        # Calculate aggregate token usage
        total_input = 0
        total_output = 0
        for state in self._node_states.values():
            if state.token_usage:
                total_input += state.token_usage.input
                total_output += state.token_usage.output
        
        # Determine overall status
        has_failed = any(s.status == NodeExecutionStatus.FAILED for s in self._node_states.values())
        has_running = any(s.status == NodeExecutionStatus.RUNNING for s in self._node_states.values())
        
        if has_failed:
            status = ExecutionStatus.FAILED
        elif has_running:
            status = ExecutionStatus.RUNNING
        else:
            status = ExecutionStatus.COMPLETED
        
        # Serialize protocol outputs for storage
        from dipeo.core.execution.node_output import serialize_protocol
        
        serialized_outputs = {}
        # Get outputs from tracker
        for node in self.diagram.nodes:
            protocol_output = self._tracker.get_last_output(node.id)
            if protocol_output:
                serialized_outputs[str(node.id)] = serialize_protocol(protocol_output)
        
        return ExecutionState(
            id=self._execution_id,
            status=status,
            diagram_id=self._diagram_id,
            started_at=datetime.now().isoformat(),
            node_states={str(k): v for k, v in self._node_states.items()},
            node_outputs=serialized_outputs,
            token_usage=TokenUsage(input=total_input, output=total_output),
            variables=self._variables.copy(),
            is_active=has_running,
            exec_counts={str(node_id): self._tracker.get_execution_count(node_id) 
                        for node_id in self._node_states.keys()},
            executed_nodes=[str(node_id) for node_id in self._tracker.get_execution_summary()["execution_order"]]
        )
    
    # ========== ExecutionTracker Integration Methods ==========
    
    def get_tracker_output(self, node_id: NodeID) -> Any:
        """Get the last output from the execution tracker."""
        return self._tracker.get_last_output(node_id)
    
    def get_tracker_execution_count(self, node_id: NodeID) -> int:
        """Get execution count from the tracker."""
        return self._tracker.get_execution_count(node_id)
    
    def has_node_executed_in_tracker(self, node_id: NodeID) -> bool:
        """Check if node has executed according to the tracker."""
        return self._tracker.has_executed(node_id)
    
    def get_execution_summary(self) -> dict[str, Any]:
        """Get execution summary from the tracker."""
        return self._tracker.get_execution_summary()
    
    def has_running_nodes(self) -> bool:
        """Check if any nodes are currently running."""
        return any(
            state.status == NodeExecutionStatus.RUNNING 
            for state in self._node_states.values()
        )
    
    def count_nodes_by_status(self, statuses: list[str]) -> int:
        """Count nodes that have one of the given statuses."""
        return sum(
            1 for state in self._node_states.values()
            if state.status in statuses
        )
    
    # ========== Required Properties ==========
    
    @property
    def diagram_id(self) -> str:
        """Get diagram ID."""
        return str(self._diagram_id) if self._diagram_id else ""
    
    @property
    def execution_id(self) -> str:
        """Get execution ID."""
        return str(self._execution_id)
    
