"""Simplified execution context using focused components.

This module provides a cleaner implementation of ExecutionContext that
delegates responsibilities to specialized managers.
"""

import logging
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from dipeo.diagram_generated import NodeID, NodeType, Status
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.domain.events import EventBus
from dipeo.domain.execution.envelope import Envelope
from dipeo.domain.execution.event_manager import EventManager
from dipeo.domain.execution.execution_context import ExecutionContext as ExecutionContextProtocol
from dipeo.domain.execution.state_tracker import StateTracker
from dipeo.domain.execution.token_manager import TokenManager

if TYPE_CHECKING:
    from dipeo.application.bootstrap import Container
    from dipeo.application.registry import ServiceRegistry

logger = logging.getLogger(__name__)


@dataclass
class TypedExecutionContext(ExecutionContextProtocol):
    """Simplified execution context with clean separation of concerns.

    This context delegates to specialized components:
    - TokenManager: Token flow and edge management
    - StateTracker: Node states and execution history
    - Core context: Service access and coordination
    """

    # Core identifiers
    execution_id: str
    diagram_id: str
    diagram: ExecutableDiagram

    # Component managers (private)
    _token_manager: TokenManager = field(init=False)
    _state_tracker: StateTracker = field(init=False)
    _event_manager: EventManager = field(init=False)

    # Runtime data
    _variables: dict[str, Any] = field(default_factory=dict)
    _metadata: dict[str, Any] = field(default_factory=dict)
    _current_node_id: NodeID | None = None
    _parent_metadata: dict[str, Any] = field(default_factory=dict)  # For nested sub-diagrams

    # Services (optional)
    service_registry: "ServiceRegistry | None" = None
    container: "Container | None" = None
    scheduler: Any = None  # Optional scheduler for notifications
    event_bus: EventBus | None = None

    def __post_init__(self):
        """Initialize domain managers."""
        # Initialize managers
        self._state_tracker = StateTracker()
        self._token_manager = TokenManager(self.diagram, execution_tracker=self._state_tracker)
        self._event_manager = EventManager(
            execution_id=self.execution_id,
            diagram_id=self.diagram_id,
            event_bus=self.event_bus,
            state_tracker=self._state_tracker,
        )

        # Configure join policies from diagram
        if self.scheduler and hasattr(self.scheduler, "configure_join_policies"):
            self.scheduler.configure_join_policies(self.diagram)

    # ========== Manager Properties ==========

    @property
    def state(self) -> StateTracker:
        """Direct access to state tracker for state operations."""
        return self._state_tracker

    @property
    def tokens(self) -> TokenManager:
        """Direct access to token manager for token operations."""
        return self._token_manager

    @property
    def events(self) -> EventManager:
        """Direct access to event manager for event operations."""
        return self._event_manager

    # ========== Epoch Management ==========

    def current_epoch(self) -> int:
        """Get the current execution epoch."""
        return self._token_manager.current_epoch()

    def begin_epoch(self) -> int:
        """Start a new epoch (for loop entry)."""
        return self._token_manager.begin_epoch()

    # ========== Context-Specific Logic ==========

    def consume_inbound(self, node_id: NodeID, epoch: int | None = None) -> dict[str, Envelope]:
        """Consume all available input tokens for a node.

        This method adds context-specific logic on top of token manager.
        """
        return self._token_manager.consume_inbound(node_id, epoch)

    def emit_outputs_as_tokens(
        self, node_id: NodeID, outputs: dict[str, Envelope], epoch: int | None = None
    ) -> None:
        """Emit node outputs as tokens on outgoing edges.

        This method adds scheduler notification on top of token manager.
        """
        import logging

        logger = logging.getLogger(__name__)

        self._token_manager.emit_outputs(node_id, outputs, epoch)

        # Notify scheduler if available
        if self.scheduler:
            if hasattr(self.scheduler, "on_token_published"):
                edges = self._token_manager._out_edges.get(node_id, [])
                for edge in edges:
                    self.scheduler.on_token_published(edge, epoch or self.current_epoch())
        else:
            logger.debug("[CONTEXT] No scheduler available")

    def has_new_inputs(self, node_id: NodeID, epoch: int | None = None) -> bool:
        """Check if a node has unconsumed tokens ready.

        This method adds join policy resolution on top of token manager.
        """
        # Get join policy for this node
        join_policy = "all"  # Default

        # First check if node has compiled join_policy
        node = self.diagram.get_node(node_id)
        if node and hasattr(node, "join_policy"):
            node_join_policy = getattr(node, "join_policy", None)
            if node_join_policy is not None:
                join_policy = node_join_policy
        # Then check if scheduler has join policy configured
        elif self.scheduler and hasattr(self.scheduler, "_join_policies"):
            policy = self.scheduler._join_policies.get(node_id)
            if policy:
                join_policy = policy.policy_type
        # Finally, fallback to type-based defaults
        elif node and hasattr(node, "type") and node.type == NodeType.CONDITION:
            join_policy = "any"

        return self._token_manager.has_new_inputs(node_id, epoch, join_policy)

    # ========== Variables ==========

    def get_variable(self, name: str) -> Any:
        """Get a variable value."""
        # Check for branch decisions first
        if name.startswith("branch[") and name.endswith("]"):
            node_id = NodeID(name[7:-1])
            return self._token_manager.get_branch_decision(node_id)
        return self._variables.get(name)

    def set_variable(self, name: str, value: Any) -> None:
        """Set a variable value."""
        self._variables[name] = value

    def get_variables(self) -> dict[str, Any]:
        """Get all variables."""
        return dict(self._variables)

    def set_variables(self, variables: dict[str, Any]) -> None:
        """Set multiple variables."""
        self._variables.update(variables)

    # ========== Metadata ==========

    def get_execution_metadata(self) -> dict[str, Any]:
        """Get execution metadata."""
        return dict(self._metadata)

    def set_execution_metadata(self, key: str, value: Any) -> None:
        """Set execution metadata."""
        self._metadata[key] = value

    def get_node_metadata(self, node_id: NodeID) -> dict[str, Any]:
        """Get node-specific metadata."""
        return self._state_tracker.get_node_metadata(node_id)

    def set_node_metadata(self, node_id: NodeID, key: str, value: Any) -> None:
        """Set node-specific metadata."""
        self._state_tracker.set_node_metadata(node_id, key, value)

    # ========== Execution State ==========

    def can_execute_in_loop(self, node_id: NodeID, epoch: int | None = None) -> bool:
        """Check if node can execute in current epoch considering loop limits.

        Returns:
            True if node can execute, False if it hit iteration limit
        """
        return self._state_tracker.can_execute_in_loop(node_id, epoch or self.current_epoch())

    @property
    def current_node_id(self) -> NodeID | None:
        """Get the currently executing node ID."""
        return self._current_node_id

    @contextmanager
    def executing_node(self, node_id: NodeID):
        """Context manager for tracking currently executing node."""
        prev = self._current_node_id
        self._current_node_id = node_id
        try:
            yield
        finally:
            self._current_node_id = prev

    def is_execution_complete(self) -> bool:
        """Check if execution is complete.

        Returns:
            True if all endpoints are completed or failed
        """
        endpoint_nodes = self.diagram.get_nodes_by_type(NodeType.ENDPOINT)
        if not endpoint_nodes:
            # No endpoints, check if all nodes are done
            all_states = self._state_tracker.get_all_node_states()
            if not all_states:
                return False

            for state in all_states.values():
                if state.status in (Status.PENDING, Status.RUNNING):
                    return False
            return True

        # Check if all endpoints are completed
        for endpoint in endpoint_nodes:
            state = self._state_tracker.get_node_state(endpoint.id)
            if not state or state.status not in (Status.COMPLETED, Status.FAILED):
                return False
        return True

    def is_first_execution(self, node_id: NodeID) -> bool:
        """Check if this is the first execution of a node."""
        return self._state_tracker.get_node_execution_count(node_id) == 0

    # ========== Template Context Building ==========

    def build_template_context(
        self,
        inputs: dict[str, Any] | None = None,
        locals_: dict[str, Any] | None = None,
        globals_win: bool = True,
    ) -> dict[str, Any]:
        """Build a consistent template context merging globals, inputs, and locals.

        This method merges variables from different scopes for use in template rendering.
        It provides both namespaced access (globals.var, inputs.var, local.var) and
        flat access (var) for ergonomic template syntax.

        Args:
            inputs: Input values from the node
            locals_: Local variables (e.g., foreach loop variables)
            globals_win: If True, globals override inputs/locals. If False, locals override.

        Returns:
            Merged context with both namespaced and flat access patterns
        """
        reserved_local_keys = {"this", "@index", "@first", "@last"}

        inputs = inputs or {}
        locals_ = locals_ or {}
        globals_ = self.get_variables()

        # Namespaced copies to avoid collisions in templates if desired
        merged = {
            "globals": {k: v for k, v in globals_.items() if k not in reserved_local_keys},
            "inputs": inputs,
            "local": locals_,
        }

        # Flat root for ergonomic {{ var }} access:
        flat = (
            {**inputs, **locals_, **globals_} if globals_win else {**globals_, **inputs, **locals_}
        )

        merged.update(flat)
        return merged

    # ========== Compatibility Methods ==========

    def get_tracker(self) -> Any:
        """Get the underlying execution tracker.

        For advanced use cases requiring direct tracker access.
        """
        return self._state_tracker._tracker
