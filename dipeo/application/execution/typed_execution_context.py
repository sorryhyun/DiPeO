"""Typed execution context with unified state management.

This module provides a concrete implementation of the ExecutionContext protocol
that manages all execution state, coordinates state transitions, and provides
a clean API for both the execution engine and node handlers.
"""

import logging
import threading
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Optional

from dipeo.diagram_generated import (
    NodeID,
    NodeState,
    Status,
)
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode
from dipeo.domain.events import DomainEvent, DomainEventBus, EventType
from dipeo.domain.execution.envelope import Envelope
from dipeo.domain.execution.execution_context import ExecutionContext as ExecutionContextProtocol
from dipeo.domain.execution.execution_tracker import CompletionStatus, ExecutionTracker
from dipeo.domain.execution.resolution import RuntimeInputResolver
from dipeo.domain.execution.token_types import EdgeRef, Token

if TYPE_CHECKING:
    from dipeo.application.bootstrap import Container
    from dipeo.application.registry import ServiceRegistry

logger = logging.getLogger(__name__)


@dataclass
class TypedExecutionContext(ExecutionContextProtocol):
    """Unified execution context managing all execution state and operations.
    
    This context provides:
    - Thread-safe state management
    - Node state transitions
    - Input/output resolution
    - Event emission
    - Service access
    - Execution tracking
    """
    
    # Core identifiers
    execution_id: str
    diagram_id: str
    diagram: ExecutableDiagram
    
    # State management (private to enforce encapsulation)
    _node_states: dict[NodeID, NodeState] = field(default_factory=dict)
    _tracker: ExecutionTracker = field(default_factory=ExecutionTracker)
    _state_lock: threading.Lock = field(default_factory=threading.Lock)
    
    # Runtime data
    _variables: dict[str, Any] = field(default_factory=dict)
    _metadata: dict[str, Any] = field(default_factory=dict)
    _current_node_id: NodeID | None = None
    
    # Node metadata storage
    _node_metadata: dict[NodeID, dict[str, Any]] = field(default_factory=dict)
    
    # Dynamic control flow
    _branch_decisions: dict[NodeID, str] = field(default_factory=dict)
    _loop_states: dict[NodeID, bool] = field(default_factory=dict)
    
    # Dependencies
    service_registry: Optional["ServiceRegistry"] = None
    runtime_resolver: RuntimeInputResolver | None = None
    event_bus: DomainEventBus | None = None
    container: Optional["Container"] = None
    scheduler: Any = None  # Reference to NodeScheduler for token events
    
    # Epoch tracking for flow control
    _epoch: int = field(default_factory=lambda: 0)
    _last_epoch_run: dict[NodeID, int] = field(default_factory=dict)
    
    # Token management
    _edge_seq: dict[tuple[EdgeRef, int], int] = field(default_factory=lambda: defaultdict(int))
    _edge_tokens: dict[tuple[EdgeRef, int, int], Envelope] = field(default_factory=dict)
    _last_consumed: dict[tuple[NodeID, EdgeRef, int], int] = field(default_factory=lambda: defaultdict(int))
    
    # Quick edge maps (initialized in __post_init__)
    _in_edges: dict[NodeID, list[EdgeRef]] = field(default_factory=dict)
    _out_edges: dict[NodeID, list[EdgeRef]] = field(default_factory=dict)
    
    # Phase 3.3: Loop control
    _node_iterations_per_epoch: dict[tuple[NodeID, int], int] = field(default_factory=lambda: defaultdict(int))
    _edge_ttl: dict[EdgeRef, int] = field(default_factory=dict)  # Time-to-live for edge tokens
    _max_iterations_per_epoch: int = 100  # Default max iterations per node per epoch
    
    def __post_init__(self):
        """Initialize edge maps from the diagram."""
        self._initialize_edge_maps()
    
    def _initialize_edge_maps(self):
        """Build incoming and outgoing edge maps for efficient lookups."""
        for edge in self.diagram.edges:
            edge_ref = EdgeRef(
                source_node_id=edge.source_node_id,
                source_output=edge.source_output,
                target_node_id=edge.target_node_id
            )
            
            # Add to outgoing edges
            if edge.source_node_id not in self._out_edges:
                self._out_edges[edge.source_node_id] = []
            self._out_edges[edge.source_node_id].append(edge_ref)
            
            # Add to incoming edges
            if edge.target_node_id not in self._in_edges:
                self._in_edges[edge.target_node_id] = []
            self._in_edges[edge.target_node_id].append(edge_ref)
    
    # ========== Token API ==========
    
    def current_epoch(self) -> int:
        """Get the current execution epoch."""
        return self._epoch
    
    def begin_epoch(self) -> int:
        """Start a new epoch (e.g., for loop entry).
        
        Phase 3.3: Allows loop controllers to bump epochs deliberately.
        
        Returns:
            The new epoch number
        """
        self._epoch += 1
        logger.info(f"[TOKEN] Beginning new epoch: {self._epoch}")
        return self._epoch
    
    def can_execute_in_loop(self, node_id: NodeID, epoch: int | None = None) -> bool:
        """Check if a node can execute within loop iteration limits.
        
        Phase 3.3: Enforces max iterations per epoch to prevent infinite loops.
        
        Args:
            node_id: The node to check
            epoch: The epoch (defaults to current)
            
        Returns:
            True if the node hasn't exceeded max iterations for this epoch
        """
        if epoch is None:
            epoch = self._epoch
            
        key = (node_id, epoch)
        current_count = self._node_iterations_per_epoch[key]
        
        # Check node-specific max iterations (e.g., PersonJobNode)
        node = self.diagram.get_node(node_id) if self.diagram else None
        if node and hasattr(node, 'max_iteration'):
            return current_count < node.max_iteration
            
        # Check global max iterations per epoch
        return current_count < self._max_iterations_per_epoch
    
    def publish_token(self, edge: EdgeRef, payload: Envelope, epoch: int | None = None) -> Token:
        """Publish a token on an edge.
        
        Args:
            edge: The edge to publish on
            payload: The envelope to send
            epoch: The epoch (defaults to current)
            
        Returns:
            The published token
        """
        if epoch is None:
            epoch = self._epoch
            
        with self._state_lock:
            # Increment sequence number for this edge/epoch
            seq_key = (edge, epoch)
            self._edge_seq[seq_key] += 1
            seq = self._edge_seq[seq_key]
            
            # Create and store the token
            token = Token(
                epoch=epoch,
                seq=seq,
                content=payload
            )
            
            # Store the envelope for later consumption
            self._edge_tokens[(edge, epoch, seq)] = payload
            
            logger.debug(f"[TOKEN] Published token on {edge.source_node_id}->{edge.target_node_id} "
                       f"(epoch={epoch}, seq={seq})")
            
            # Signal the scheduler if available (Phase 2.1 integration)
            if self.scheduler and hasattr(self.scheduler, 'on_token_published'):
                self.scheduler.on_token_published(edge, epoch)
            
            return token
    
    def get_inbound_tokens(self, node_id: NodeID, epoch: int | None = None) -> dict[EdgeRef, tuple[int, Envelope]]:
        """Get the latest tokens on all inbound edges without consuming them.
        
        Args:
            node_id: The node to check
            epoch: The epoch (defaults to current)
            
        Returns:
            Map of edge to (seq, envelope)
        """
        if epoch is None:
            epoch = self._epoch
            
        result = {}
        with self._state_lock:
            for edge in self._in_edges.get(node_id, []):
                seq = self._edge_seq[(edge, epoch)]
                if seq > 0:
                    envelope = self._edge_tokens.get((edge, epoch, seq))
                    if envelope is not None:
                        result[edge] = (seq, envelope)
        return result
    
    def has_new_inputs(self, node_id: NodeID, epoch: int | None = None) -> bool:
        """Check if a node has new inputs to process.
        
        Phase 3.2: Respects join policies (all, any, k_of_n).
        
        Args:
            node_id: The node to check
            epoch: The epoch (defaults to current)
            
        Returns:
            True if the node has unconsumed tokens on required edges per join policy
        """
        if epoch is None:
            epoch = self._epoch
            
        edges = self._in_edges.get(node_id, [])
        if not edges:
            # Source nodes are always ready
            return True
        
        # Get join policy for this node (default to 'all' for backward compatibility)
        from dipeo.domain.execution.token_types import JoinPolicy
        join_policy = JoinPolicy(policy_type="all")  # Default
        
        # Check if scheduler has join policy configured
        if hasattr(self, 'scheduler') and self.scheduler:
            node_policy = self.scheduler._join_policies.get(node_id)
            if node_policy:
                join_policy = node_policy
        
        # Separate conditional and non-conditional edges
        conditional_edges = []
        non_conditional_edges = []
        for edge in edges:
            if edge.source_output in ["condtrue", "condfalse"]:
                conditional_edges.append(edge)
            else:
                non_conditional_edges.append(edge)
        
        # Count edges with new tokens
        new_token_count = 0
        edges_to_check = non_conditional_edges  # Default to non-conditional
        
        # For conditional edges, only check active branches
        if conditional_edges:
            for edge in conditional_edges:
                # Check if this branch is active
                branch_var = self.get_variable(f"branch[{edge.source_node_id}]")
                if branch_var == edge.source_output:
                    edges_to_check.append(edge)
        
        # Apply join policy
        if join_policy.policy_type == "all":
            # ALL: Require new tokens on all active edges
            for edge in edges_to_check:
                seq = self._edge_seq[(edge, epoch)]
                last_consumed = self._last_consumed[(node_id, edge, epoch)]
                if seq <= last_consumed:
                    return False  # Missing token on required edge
            return len(edges_to_check) > 0  # Must have at least one edge
            
        elif join_policy.policy_type == "any":
            # ANY: Require new token on at least one edge
            for edge in edges_to_check:
                seq = self._edge_seq[(edge, epoch)]
                last_consumed = self._last_consumed[(node_id, edge, epoch)]
                if seq > last_consumed:
                    return True  # Found at least one new token
            return False
            
        elif join_policy.policy_type == "k_of_n" and join_policy.k:
            # K_OF_N: Require new tokens on at least K edges
            k = join_policy.k
            for edge in edges_to_check:
                seq = self._edge_seq[(edge, epoch)]
                last_consumed = self._last_consumed[(node_id, edge, epoch)]
                if seq > last_consumed:
                    new_token_count += 1
                    if new_token_count >= k:
                        return True
            return False
            
        # Fallback to ALL
        return all(
            self._edge_seq[(edge, epoch)] > self._last_consumed[(node_id, edge, epoch)]
            for edge in edges_to_check
        ) if edges_to_check else False
    
    def consume_inbound(self, node_id: NodeID, epoch: int | None = None) -> dict[str, Envelope]:
        """Atomically consume inbound tokens for a node.
        
        Args:
            node_id: The node consuming tokens
            epoch: The epoch (defaults to current)
            
        Returns:
            Map of port name to envelope
        """
        if epoch is None:
            epoch = self._epoch
            
        inputs: dict[str, Envelope] = {}
        with self._state_lock:
            for edge in self._in_edges.get(node_id, []):
                seq = self._edge_seq[(edge, epoch)]
                if seq == 0:
                    continue
                    
                # Mark as consumed
                self._last_consumed[(node_id, edge, epoch)] = seq
                
                # Get the payload
                payload = self._edge_tokens.get((edge, epoch, seq))
                if payload is not None:
                    # Use source_output as the port key, default to "default"
                    key = edge.source_output or "default"
                    inputs[key] = payload
                    
            logger.debug(f"[TOKEN] Node {node_id} consumed {len(inputs)} inputs for epoch {epoch}")
        
        return inputs
    
    def emit_outputs_as_tokens(self, node_id: NodeID, outputs: dict[str, Envelope], epoch: int | None = None) -> None:
        """Compatibility helper to emit handler outputs as tokens.
        
        Phase 3.1: Filters conditional branches - only publishes tokens on active branches.
        
        Args:
            node_id: The node emitting outputs
            outputs: Map of output port to envelope
            epoch: The epoch (defaults to current)
        """
        if epoch is None:
            epoch = self._epoch
            
        # Check if this is a condition node emitting branches
        node = self.diagram.get_node(node_id) if self.diagram else None
        is_condition = node and hasattr(node, 'type') and str(node.type).lower() == 'condition'
        
        # Determine active branch if this is a condition node
        active_branch = None
        if is_condition and "default" in outputs:
            # Extract condition result from output
            output = outputs["default"]
            if hasattr(output, 'body'):
                body = output.body
                if isinstance(body, dict) and "result" in body:
                    active_branch = "condtrue" if bool(body["result"]) else "condfalse"
                elif isinstance(body, bool):
                    active_branch = "condtrue" if body else "condfalse"
            
            # Store branch decision for downstream nodes
            if active_branch:
                self.set_variable(f"branch[{node_id}]", active_branch)
                logger.debug(f"[TOKEN] Condition node {node_id} selected branch: {active_branch}")
        
        for edge in self._out_edges.get(node_id, []):
            # Phase 3.1: Filter non-selected branches for condition nodes
            if is_condition and active_branch:
                # Only emit on the active branch
                if edge.source_output not in [active_branch, None, "default"]:
                    logger.debug(f"[TOKEN] Skipping inactive branch {edge.source_output} from {node_id}")
                    continue
            
            # Match output port or use default
            out_key = edge.source_output or "default"
            payload = outputs.get(out_key) or outputs.get("default")
            
            if payload is None:
                logger.debug(f"[TOKEN] No output for port {out_key} on edge from {node_id}")
                continue
                
            self.publish_token(edge, payload, epoch=epoch)
    
    # ========== Node State Queries ==========
    
    def get_node_state(self, node_id: NodeID) -> NodeState | None:
        """Get the current state of a node."""
        with self._state_lock:
            return self._node_states.get(node_id)
    
    def get_node_result(self, node_id: NodeID) -> dict[str, Any] | None:
        """Get the execution result of a completed node."""
        envelope = self._tracker.get_last_output(node_id)
        if envelope:
            result = {"value": envelope.body}
            if envelope.meta:
                result["metadata"] = envelope.meta
            return result
        return None
    
    def get_node_output(self, node_id: NodeID) -> Envelope | None:
        """Get the typed output of a completed node."""
        return self._tracker.get_last_output(node_id)
    
    def get_all_node_states(self) -> dict[NodeID, NodeState]:
        """Get all node states in the execution context."""
        with self._state_lock:
            return dict(self._node_states)
    
    # ========== Execution Status Queries ==========
    
    def get_completed_nodes(self) -> list[NodeID]:
        """Get all nodes that have completed execution."""
        with self._state_lock:
            return [
                node_id for node_id, state in self._node_states.items()
                if state.status == Status.COMPLETED
            ]
    def get_running_nodes(self) -> list[NodeID]:
        """Get nodes currently in execution."""
        with self._state_lock:
            return [
                node_id for node_id, state in self._node_states.items()
                if state.status == Status.RUNNING
            ]
    
    def get_failed_nodes(self) -> list[NodeID]:
        """Get nodes that failed during execution."""
        with self._state_lock:
            return [
                node_id for node_id, state in self._node_states.items()
                if state.status == Status.FAILED
            ]
    
    def get_node_execution_count(self, node_id: NodeID) -> int:
        """Get the number of times a node has been executed."""
        return self._tracker.get_execution_count(node_id)
    
    # ========== State Transitions ==========
    
    def transition_node_to_running(self, node_id: NodeID) -> int:
        """Transition a node to running state. Returns execution count.
        
        Phase 3.3: Tracks iterations per epoch for loop control.
        """
        with self._state_lock:
            self._node_states[node_id] = NodeState(status=Status.RUNNING)
            self._tracker.start_execution(node_id)
            
            # Track iterations per epoch for loop control (Phase 3.3)
            key = (node_id, self._epoch)
            self._node_iterations_per_epoch[key] += 1
            
            return self._tracker.get_execution_count(node_id)
    
    def transition_node_to_completed(self, node_id: NodeID, output: Any = None, token_usage: dict[str, int] | None = None) -> None:
        """Transition a node to completed state with output."""
        with self._state_lock:
            self._node_states[node_id] = NodeState(status=Status.COMPLETED)
            self._tracker.complete_execution(
                node_id, 
                CompletionStatus.SUCCESS, 
                output=output,
                token_usage=token_usage
            )
        
        # Handle downstream resets for loops (only for successful completion)
        self._reset_downstream_nodes_if_needed(node_id)
    
    def transition_node_to_failed(self, node_id: NodeID, error: str) -> None:
        """Transition a node to failed state with error message."""
        with self._state_lock:
            self._node_states[node_id] = NodeState(
                status=Status.FAILED,
                error=error
            )
            self._tracker.complete_execution(
                node_id,
                CompletionStatus.FAILED,
                error=error
            )
    
    def transition_node_to_maxiter(self, node_id: NodeID, output: Envelope | None = None) -> None:
        """Transition a node to max iterations state."""
        logger.debug(f"[MAXITER] Transitioning {node_id} to MAXITER_REACHED")
        with self._state_lock:
            self._node_states[node_id] = NodeState(status=Status.MAXITER_REACHED)
            self._tracker.complete_execution(
                node_id,
                CompletionStatus.MAX_ITER,
                output=output
            )
    
    def transition_node_to_skipped(self, node_id: NodeID) -> None:
        """Transition a node to skipped state."""
        with self._state_lock:
            self._node_states[node_id] = NodeState(status=Status.SKIPPED)
            self._tracker.complete_execution(
                node_id,
                CompletionStatus.SKIPPED
            )
    
    def reset_node(self, node_id: NodeID) -> None:
        """Reset a node to initial state."""
        with self._state_lock:
            self._node_states[node_id] = NodeState(status=Status.PENDING)
            # Note: We do NOT reset the execution count in the tracker
            # The tracker maintains cumulative execution count across resets
            logger.debug(f"Reset node {node_id} to PENDING, execution_count remains {self._tracker.get_execution_count(node_id)}")
    
    def _reset_downstream_nodes_if_needed(self, node_id: NodeID, initiating_node_id: NodeID = None) -> None:
        """Reset downstream nodes if they're part of a loop.
        
        Args:
            node_id: The node that just completed
            initiating_node_id: The original node that started the reset chain (to prevent circular resets)
        """
        from dipeo.diagram_generated.generated_nodes import (
            ConditionNode,
            EndpointNode,
            PersonJobNode,
            StartNode,
        )

        # Track the initiating node to prevent circular resets
        if initiating_node_id is None:
            initiating_node_id = node_id

        # Get the node that just completed
        completed_node = self.diagram.get_node(node_id)

        # Special handling for ConditionNode - only reset nodes on the active branch
        if isinstance(completed_node, ConditionNode):
            # (A) Preferred: read from global variables
            active_branch = None
            if hasattr(self, "get_variable"):
                active_branch = self.get_variable(f"branch[{node_id}]")
            
            # (B) Fallback: infer from legacy patterns if needed
            if not active_branch:
                output = self._tracker.get_last_output(node_id)
                from dipeo.domain.execution.envelope import Envelope
                if isinstance(output, Envelope) and output and isinstance(output.body, dict) and "result" in output.body:
                    active_branch = "condtrue" if bool(output.body["result"]) else "condfalse"
            
            if not active_branch:
                # Default safe branch
                active_branch = "condfalse"

            # Only process edges on the active branch
            all_outgoing = self.diagram.get_outgoing_edges(node_id)
            outgoing_edges = [
                e for e in all_outgoing
                if e.source_output == active_branch
            ]
        else:
            # For non-condition nodes, process all outgoing edges as before
            outgoing_edges = self.diagram.get_outgoing_edges(node_id)
        
        nodes_to_reset = []
        
        for edge in outgoing_edges:
            target_node = self.diagram.get_node(edge.target_node_id)
            if not target_node:
                continue
            
            # Skip if this would cause a circular reset
            if target_node.id == initiating_node_id:
                logger.debug(f"Skipping reset of {target_node.id} to prevent circular reset")
                continue
            
            # Check if target was already executed
            target_state = self._node_states.get(target_node.id)
            if not target_state or target_state.status != Status.COMPLETED:
                continue
            
            # Check if we can reset this node
            can_reset = True
            
            # Don't reset one-time nodes
            if isinstance(target_node, (StartNode, EndpointNode)):
                can_reset = False
            
            # For condition nodes, allow reset if they're part of a loop
            # Check if any of its outgoing edges point back to an already-executed node
            if isinstance(target_node, ConditionNode):
                cond_outgoing = self.diagram.get_outgoing_edges(target_node.id)
                # Check if this condition has a loop back (at least one edge points to an executed node)
                has_loop_back = False
                for edge in cond_outgoing:
                    loop_target = self.diagram.get_node(edge.target_node_id)
                    if loop_target and self._tracker.get_execution_count(edge.target_node_id) > 0:
                        has_loop_back = True
                        break
                can_reset = has_loop_back
            
            # For PersonJobNodes, check max_iteration
            if isinstance(target_node, PersonJobNode):
                exec_count = self._tracker.get_execution_count(target_node.id)
                if exec_count >= target_node.max_iteration:
                    can_reset = False
            
            if can_reset:
                nodes_to_reset.append(target_node.id)

        # Reset nodes and cascade, passing the initiating node to prevent circular resets
        for node_id_to_reset in nodes_to_reset:
            self.reset_node(node_id_to_reset)
            # Cascade resets but prevent circular resets by tracking the initiator
            self._reset_downstream_nodes_if_needed(node_id_to_reset, initiating_node_id)
    
    # ========== Epoch and Path Reset ==========
    
    def begin_epoch(self, start_node_id: NodeID, endpoints: list[NodeID] | None = None) -> list[NodeID]:
        """Start a new flow epoch and reset reachable nodes on the start→endpoint path."""
        from dipeo.diagram_generated import Status
        self._epoch += 1

        path_nodes = self._compute_reachable_nodes(start_node_id, endpoints)

        with self._state_lock:
            for nid in path_nodes:
                st = self._node_states.get(nid)
                if st and st.status in {Status.COMPLETED, Status.SKIPPED, Status.FAILED, Status.PAUSED}:
                    # Do not touch RUNNING nodes to avoid preemption
                    self.reset_node(nid)
                # Track that this node can run in this epoch
                self._last_epoch_run[nid] = self._epoch

        logger.info(f"[EPOCH] Started epoch {self._epoch}, reset {len(path_nodes)} reachable nodes from {start_node_id}")
        return path_nodes

    def _compute_reachable_nodes(self, start_id: NodeID, endpoints: list[NodeID] | None) -> list[NodeID]:
        """Lightweight BFS over non-conditional edges to get the flow path.
           If endpoints provided, we can early-stop upon reaching any of them."""
        diagram = self.diagram
        # Build outgoing edges map if needed
        out_edges = {}
        for edge in diagram.edges:
            if edge.source_node_id not in out_edges:
                out_edges[edge.source_node_id] = []
            out_edges[edge.source_node_id].append(edge)
        
        seen, q = set(), [start_id]
        seen.add(start_id)
        order = []

        while q:
            u = q.pop(0)
            order.append(u)
            for e in out_edges.get(u, []):
                # Skip explicit conditional label edges if you want; or keep it simple and include all
                v = e.target_node_id
                if v not in seen:
                    seen.add(v)
                    q.append(v)

        if endpoints:
            # Optionally trim to nodes that are on at least one path to an endpoint
            # (left simple: return order as-is; good enough for minimal viable behavior)
            pass

        return order
    
    # ========== Runtime Context ==========
    
    def get_execution_metadata(self) -> dict[str, Any]:
        """Get global execution metadata."""
        return self._metadata.copy()
    
    def set_execution_metadata(self, key: str, value: Any) -> None:
        """Set a value in global execution metadata."""
        self._metadata[key] = value
    
    def get_node_metadata(self, node_id: NodeID) -> dict[str, Any]:
        """Get metadata for a specific node."""
        return self._node_metadata.get(node_id, {}).copy()
    
    def set_node_metadata(self, node_id: NodeID, key: str, value: Any) -> None:
        """Set metadata for a specific node."""
        if node_id not in self._node_metadata:
            self._node_metadata[node_id] = {}
        self._node_metadata[node_id][key] = value
    
    # ========== Dynamic Control Flow ==========
    
    def mark_branch_taken(self, node_id: NodeID, branch: str) -> None:
        """Mark which branch was taken from a conditional node."""
        self._branch_decisions[node_id] = branch
    
    def get_branch_taken(self, node_id: NodeID) -> str | None:
        """Get which branch was taken from a conditional node."""
        return self._branch_decisions.get(node_id)
    
    def is_loop_active(self, node_id: NodeID) -> bool:
        """Check if a loop node should continue iterating."""
        return self._loop_states.get(node_id, True)
    
    def update_loop_state(self, node_id: NodeID, should_continue: bool) -> None:
        """Update the iteration state of a loop node."""
        self._loop_states[node_id] = should_continue
    
    # ========== Additional Context Methods ==========
    
    def get_variable(self, name: str) -> Any:
        """Get a variable value."""
        return self._variables.get(name)
    
    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable value."""
        self._variables[name] = value
    
    
    @property
    def current_node_id(self) -> NodeID | None:
        """Get the currently executing node ID."""
        return self._current_node_id
    
    @contextmanager
    def executing_node(self, node_id: NodeID):
        """Context manager for node execution."""
        old_node = self._current_node_id
        self._current_node_id = node_id
        try:
            yield
        finally:
            self._current_node_id = old_node
    
    # ========== Execution Queries ==========
    
    def is_execution_complete(self) -> bool:
        """Check if execution is complete."""
        # Check if any endpoint nodes have been reached
        from dipeo.diagram_generated.generated_nodes import NodeType
        has_endpoint = False
        endpoints = self.diagram.get_nodes_by_type(NodeType.ENDPOINT)
        for node in endpoints:
                has_endpoint = True
                node_state = self.get_node_state(node.id)
                if node_state and node_state.status in [Status.COMPLETED, Status.MAXITER_REACHED]:
                    return True
        
        # Check if any nodes are running
        if any(state.status == Status.RUNNING for state in self._node_states.values()):
            return False
        
        # If there's an endpoint node but it hasn't been executed yet, execution is not complete
        if has_endpoint:
            # Check if endpoint dependencies are met but endpoint hasn't run
            for node in endpoints:
                    node_state = self.get_node_state(node.id)
                    # If endpoint has no state yet, execution is not complete
                    if not node_state:
                        return False
        
        # Check if all nodes have been processed (no pending nodes with met dependencies)
        # This is a simplified check - the engine's order calculator determines actual readiness
        has_pending = any(state.status == Status.PENDING for state in self._node_states.values())
        return not has_pending
    
    
    
    # ========== Input Resolution ==========
    
    def resolve_node_inputs(self, node: ExecutableNode) -> dict[str, Any]:
        """Resolve inputs for a node using the runtime resolver."""
        if not self.runtime_resolver:
            return {}
        
        # Get incoming edges
        incoming_edges = self.diagram.get_incoming_edges(node.id)
        
        # Build resolver context (self implements the protocol)
        return self.runtime_resolver.resolve_node_inputs(
            node=node,
            incoming_edges=incoming_edges,
            context=self
        )
    
    # ========== Event Management ==========
    
    async def emit_event(self, event_type: EventType, data: dict[str, Any] | None = None) -> None:
        """Emit an event through the event bus."""
        if not self.event_bus:
            return
        
        # Import factory functions and classes
        from dipeo.domain.events import (
            EventScope,
            NodeOutputPayload,
            execution_completed,
            execution_error,
            execution_started,
            node_completed,
            node_error,
            node_started,
        )
        
        processed_data = data or {}
        
        # Create the appropriate event based on type
        event = None
        
        if event_type == EventType.EXECUTION_STARTED:
            event = execution_started(
                execution_id=self.execution_id,
                variables=processed_data.get('variables', {}),
                initiated_by=processed_data.get('initiated_by'),
                diagram_id=processed_data.get('diagram_id')
            )
        
        elif event_type == EventType.EXECUTION_COMPLETED:
            event = execution_completed(
                execution_id=self.execution_id,
                status=processed_data.get('status'),
                total_duration_ms=processed_data.get('total_duration_ms'),
                total_tokens_used=processed_data.get('total_tokens_used'),
                node_count=processed_data.get('node_count')
            )
        
        elif event_type == EventType.EXECUTION_ERROR:
            event = execution_error(
                execution_id=self.execution_id,
                error_message=processed_data.get('error', 'Unknown error'),
                error_type=processed_data.get('error_type'),
                stack_trace=processed_data.get('stack_trace'),
                failed_node_id=processed_data.get('failed_node_id')
            )
        
        elif event_type == EventType.NODE_STARTED:
            node_id = processed_data.get('node_id')
            if node_id:
                event = node_started(
                    execution_id=self.execution_id,
                    node_id=node_id,
                    state=processed_data.get('state'),
                    node_type=processed_data.get('node_type'),
                    inputs=processed_data.get('inputs'),
                    iteration=processed_data.get('iteration')
                )
        
        elif event_type == EventType.NODE_COMPLETED:
            node_id = processed_data.get('node_id')
            if node_id:
                event = node_completed(
                    execution_id=self.execution_id,
                    node_id=node_id,
                    state=processed_data.get('state'),
                    output=processed_data.get('output'),
                    duration_ms=processed_data.get('metrics', {}).get('duration_ms') if processed_data.get('metrics') else None,
                    token_usage=processed_data.get('metrics', {}).get('token_usage') if processed_data.get('metrics') else None,
                    output_summary=processed_data.get('output_summary')
                )
        
        elif event_type == EventType.NODE_ERROR:
            node_id = processed_data.get('node_id')
            if node_id:
                event = node_error(
                    execution_id=self.execution_id,
                    node_id=node_id,
                    state=processed_data.get('state'),
                    error_message=processed_data.get('error', 'Unknown error'),
                    error_type=processed_data.get('error_type'),
                    retryable=processed_data.get('retryable', False),
                    retry_count=processed_data.get('retry_count', 0),
                    max_retries=processed_data.get('max_retries', 3)
                )
        
        elif event_type == EventType.NODE_OUTPUT:
            node_id = processed_data.get('node_id')
            if node_id:
                # NODE_OUTPUT needs manual creation as there's no factory function
                event = DomainEvent(
                    type=EventType.NODE_OUTPUT,
                    scope=EventScope(
                        execution_id=self.execution_id,
                        node_id=node_id
                    ),
                    payload=NodeOutputPayload(
                        output=processed_data.get('output'),
                        is_partial=processed_data.get('is_partial', False),
                        sequence_number=processed_data.get('sequence_number')
                    )
                )
        
        if event:
            await self.event_bus.publish(event)
    
    # ========== Event Helper Methods ==========
    
    async def emit_execution_started(self, diagram_name: str | None = None) -> None:
        """Emit execution started event with minimal data."""
        await self.emit_event(
            EventType.EXECUTION_STARTED,
            {
                "diagram_id": self.diagram_id,
                "diagram_name": diagram_name or self.diagram.metadata.get("name", "unknown") if self.diagram.metadata else "unknown"
            }
        )
    
    async def emit_execution_completed(self, status: Any = None, total_steps: int = 0, execution_path: list[str] | None = None) -> None:
        """Emit execution completed event."""
        from dipeo.diagram_generated import Status
        await self.emit_event(
            EventType.EXECUTION_COMPLETED,
            {
                "status": status or Status.COMPLETED,
                "total_steps": total_steps,
                "execution_path": execution_path or []
            }
        )
    
    async def emit_execution_error(self, exc: Exception) -> None:
        """Emit execution error event."""
        await self.emit_event(
            EventType.EXECUTION_ERROR,
            {
                "error": str(exc),
                "error_type": type(exc).__name__
            }
        )
    
    async def emit_node_started(self, node: ExecutableNode) -> None:
        """Emit node started event."""
        await self.emit_event(
            EventType.NODE_STARTED,
            {
                "node_id": str(node.id),
                "node_type": node.type,
                "node_name": getattr(node, 'name', str(node.id))
            }
        )
    
    async def emit_node_completed(self, node: ExecutableNode, envelope: Envelope | None, exec_count: int) -> None:
        """Emit node completed event with envelope data."""
        event_data = {
            "node_id": str(node.id),
            "node_type": node.type,
            "node_name": getattr(node, 'name', str(node.id)),
            "execution_count": exec_count
        }
        
        if envelope:
            # Serialize output
            if hasattr(envelope.body, 'dict'):
                output = envelope.body.dict()
            elif hasattr(envelope.body, 'model_dump'):
                output = envelope.body.model_dump()
            elif isinstance(envelope.body, dict):
                output = envelope.body
            else:
                output = {"value": str(envelope.body)}
            
            event_data["output"] = output
            event_data["output_summary"] = str(envelope.body)[:100] if envelope.body else ""
            
            # Extract metrics from envelope meta
            if envelope.meta:
                event_data["metrics"] = {
                    "execution_time_ms": envelope.meta.get("execution_time_ms", 0),
                    "execution_count": exec_count
                }
                # Extract token usage if present
                if "token_usage" in envelope.meta:
                    event_data["metrics"]["token_usage"] = envelope.meta["token_usage"]
        else:
            # For maxiter or other special cases without envelope
            event_data["output"] = {"value": "", "status": "MAXITER_REACHED"}
            event_data["metrics"] = {
                "execution_time_ms": 0,
                "execution_count": exec_count
            }
        
        await self.emit_event(EventType.NODE_COMPLETED, event_data)
    
    async def emit_node_error(self, node: ExecutableNode, exc: Exception) -> None:
        """Emit node error event."""
        await self.emit_event(
            EventType.NODE_ERROR,
            {
                "node_id": str(node.id),
                "node_type": node.type,
                "node_name": getattr(node, 'name', str(node.id)),
                "error": str(exc),
                "error_type": type(exc).__name__
            }
        )
    
    # ========== State Access (for persistence) ==========
    
    def get_node_states(self) -> dict[NodeID, NodeState]:
        """Get all node states for persistence."""
        with self._state_lock:
            return self._node_states.copy()
    
    def get_tracker(self) -> ExecutionTracker:
        """Get execution tracker for persistence."""
        return self._tracker
    
    def get_variables(self) -> dict[str, Any]:
        """Get execution variables."""
        return self._variables
    
    def set_variables(self, variables: dict[str, Any]) -> None:
        """Set execution variables."""
        self._variables = variables
    
    
    # ========== Handler Support Methods ==========
    
    
    def has_running_nodes(self) -> bool:
        """Check if any nodes are currently running."""
        return len(self.get_running_nodes()) > 0
    
    def get_node(self, node_id: NodeID) -> ExecutableNode | None:
        """Get node by ID from diagram."""
        return self.diagram.get_node(node_id)
    
    def is_first_execution(self, node_id: NodeID) -> bool:
        """Check if this is the first execution of a node."""
        return self.get_node_execution_count(node_id) <= 1