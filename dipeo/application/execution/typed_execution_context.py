"""Simplified execution context using focused components."""

import logging

from dipeo.config.base_logger import get_module_logger
from collections import defaultdict
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

from dipeo.diagram_generated import NodeID, NodeType, Status
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.domain.events.unified_ports import EventBus
from dipeo.domain.execution.envelope import Envelope
from dipeo.application.execution.event_pipeline import EventPipeline
from dipeo.domain.execution.execution_context import ExecutionContext as ExecutionContextProtocol
from dipeo.domain.execution.state_tracker import StateTracker
from dipeo.domain.execution.token_manager import TokenManager

if TYPE_CHECKING:
    from dipeo.application.bootstrap import Container
    from dipeo.application.registry import ServiceRegistry

logger = get_module_logger(__name__)

@dataclass
class TypedExecutionContext(ExecutionContextProtocol):
    """Simplified execution context with clean separation of concerns."""

    # Core identifiers
    execution_id: str
    diagram_id: str
    diagram: ExecutableDiagram

    _token_manager: TokenManager = field(init=False)
    _state_tracker: StateTracker = field(init=False)
    _event_pipeline: EventPipeline = field(init=False)
    _variables: dict[str, Any] = field(default_factory=dict)
    _metadata: dict[str, Any] = field(default_factory=dict)
    _current_node_id: NodeID | None = None
    _parent_metadata: dict[str, Any] = field(default_factory=dict)
    _scope_stack: list[str] = field(default_factory=list)
    _scoped_vars: dict[str, dict[str, Any]] = field(default_factory=lambda: defaultdict(dict))
    service_registry: "ServiceRegistry | None" = None
    container: "Container | None" = None
    scheduler: Any = None
    event_bus: EventBus | None = None

    def __post_init__(self):
        self._state_tracker = StateTracker()
        self._token_manager = TokenManager(self.diagram, execution_tracker=self._state_tracker)
        self._event_pipeline = EventPipeline(
            execution_id=self.execution_id,
            diagram_id=self.diagram_id,
            event_bus=self.event_bus,
            state_tracker=self._state_tracker,
        )

        if self.scheduler and hasattr(self.scheduler, "configure_join_policies"):
            self.scheduler.configure_join_policies(self.diagram)

    @property
    def state(self) -> StateTracker:
        return self._state_tracker

    @property
    def tokens(self) -> TokenManager:
        return self._token_manager

    @property
    def events(self) -> EventPipeline:
        return self._event_pipeline

    def current_epoch(self) -> int:
        return self._token_manager.current_epoch()

    def begin_epoch(self) -> int:
        return self._token_manager.begin_epoch()

    def consume_inbound(self, node_id: NodeID, epoch: int | None = None) -> dict[str, Envelope]:
        return self._token_manager.consume_inbound(node_id, epoch)

    def emit_outputs_as_tokens(
        self, node_id: NodeID, outputs: dict[str, Envelope], epoch: int | None = None
    ) -> None:
        self._token_manager.emit_outputs(node_id, outputs, epoch)

        if self.scheduler:
            if hasattr(self.scheduler, "on_token_published"):
                edges = self._token_manager._out_edges.get(node_id, [])
                for edge in edges:
                    self.scheduler.on_token_published(edge, epoch or self.current_epoch())
        else:
            logger.debug("[CONTEXT] No scheduler available")

    def has_new_inputs(self, node_id: NodeID, epoch: int | None = None) -> bool:
        join_policy = "all"
        node = self.diagram.get_node(node_id)

        if node and hasattr(node, "join_policy"):
            node_join_policy = getattr(node, "join_policy", None)
            if node_join_policy is not None:
                join_policy = node_join_policy
        elif self.scheduler and hasattr(self.scheduler, "_join_policies"):
            policy = self.scheduler._join_policies.get(node_id)
            if policy:
                join_policy = policy.policy_type
        elif node and hasattr(node, "type") and node.type == NodeType.CONDITION:
            join_policy = "any"

        return self._token_manager.has_new_inputs(node_id, epoch, join_policy)

    @contextmanager
    def enter_scope(self, name: str):
        self._scope_stack.append(name)
        try:
            yield
        finally:
            self._scope_stack.pop()
            self._scoped_vars.pop(name, None)

    def set_var(self, key: str, value: Any) -> None:
        scope = self._scope_stack[-1] if self._scope_stack else ""
        if scope:
            self._scoped_vars[scope][key] = value
        else:
            self._variables[key] = value

    def get_variable(self, name: str) -> Any:
        if name.startswith("branch[") and name.endswith("]"):
            node_id = NodeID(name[7:-1])
            return self._token_manager.get_branch_decision(node_id)

        if self._scope_stack:
            scope = self._scope_stack[-1]
            if scope in self._scoped_vars and name in self._scoped_vars[scope]:
                return self._scoped_vars[scope][name]

        return self._variables.get(name)

    def set_variable(self, name: str, value: Any) -> None:
        self.set_var(name, value)

    def get_variables(self) -> dict[str, Any]:
        result = dict(self._variables)

        if self._scope_stack:
            scope = self._scope_stack[-1]
            if scope in self._scoped_vars:
                result.update(self._scoped_vars[scope])

        return result

    def set_variables(self, variables: dict[str, Any]) -> None:
        for key, value in variables.items():
            self.set_var(key, value)

    def get_execution_metadata(self) -> dict[str, Any]:
        return dict(self._metadata)

    def set_execution_metadata(self, key: str, value: Any) -> None:
        self._metadata[key] = value

    def get_node_metadata(self, node_id: NodeID) -> dict[str, Any]:
        return self._state_tracker.get_node_metadata(node_id)

    def set_node_metadata(self, node_id: NodeID, key: str, value: Any) -> None:
        self._state_tracker.set_node_metadata(node_id, key, value)

    def can_execute_in_loop(self, node_id: NodeID, epoch: int | None = None) -> bool:
        return self._state_tracker.can_execute_in_loop(node_id, epoch or self.current_epoch())

    @property
    def current_node_id(self) -> NodeID | None:
        return self._current_node_id

    @contextmanager
    def executing_node(self, node_id: NodeID):
        prev = self._current_node_id
        self._current_node_id = node_id
        try:
            yield
        finally:
            self._current_node_id = prev

    def is_execution_complete(self) -> bool:
        endpoint_nodes = self.diagram.get_nodes_by_type(NodeType.ENDPOINT)
        if not endpoint_nodes:
            all_states = self._state_tracker.get_all_node_states()
            if not all_states:
                return False

            for state in all_states.values():
                if state.status in (Status.PENDING, Status.RUNNING):
                    return False
            return True

        for endpoint in endpoint_nodes:
            state = self._state_tracker.get_node_state(endpoint.id)
            if not state or state.status not in (Status.COMPLETED, Status.FAILED):
                return False
        return True

    def is_first_execution(self, node_id: NodeID) -> bool:
        return self._state_tracker.get_node_execution_count(node_id) == 0

    def build_template_context(
        self,
        inputs: dict[str, Any] | None = None,
        locals_: dict[str, Any] | None = None,
        globals_win: bool = True,
    ) -> dict[str, Any]:
        reserved_local_keys = {"this", "@index", "@first", "@last"}

        inputs = inputs or {}
        locals_ = locals_ or {}
        globals_ = self.get_variables()

        scope_overlay = {}
        if self._scope_stack:
            scope = self._scope_stack[-1]
            scope_overlay = self._scoped_vars.get(scope, {})

        merged = {
            "globals": {k: v for k, v in globals_.items() if k not in reserved_local_keys},
            "inputs": inputs,
            "local": locals_,
        }

        if globals_win:
            flat = {**inputs, **locals_, **globals_, **scope_overlay}
        else:
            flat = {**globals_, **inputs, **locals_, **scope_overlay}

        merged.update(flat)
        return merged

    def get_tracker(self) -> Any:
        return self._state_tracker._tracker
