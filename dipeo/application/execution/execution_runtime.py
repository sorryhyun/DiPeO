
import logging
import threading
from typing import TYPE_CHECKING, Any, Optional, Union

from dipeo.core.execution.execution_tracker import ExecutionTracker
from dipeo.diagram_generated import (
    ExecutionState,
    NodeExecutionStatus,
    NodeID,
    NodeState,
)

from dipeo.application.execution.states.node_readiness_checker import NodeReadinessChecker
from dipeo.application.execution.states.state_transition_mixin import StateTransitionMixin
from dipeo.application.execution.states.execution_state_persistence import ExecutionStatePersistence

if TYPE_CHECKING:
    from dipeo.application.registry import ServiceRegistry, ServiceKey
    from dipeo.core.static.executable_diagram import ExecutableDiagram, ExecutableNode
    from dipeo.application.bootstrap import Container

logger = logging.getLogger(__name__)


class ExecutionRuntime(StateTransitionMixin):
    
    def __init__(
        self,
        diagram: "ExecutableDiagram",
        execution_state: ExecutionState,
        service_registry: "ServiceRegistry",
        container: Optional["Container"] = None,
    ):
        self.diagram = diagram
        self._execution_id = execution_state.id
        self._diagram_id = execution_state.diagram_id
        self._service_registry = service_registry
        self._container = container
        
        self._node_states: dict[NodeID, NodeState] = {}
        self._current_node_id: list[Optional[NodeID]] = [None]
        self.metadata: dict[str, Any] = {}
        self._variables: dict[str, Any] = execution_state.variables or {}
        
        self._tracker = ExecutionTracker()
        self._state_lock = threading.Lock()
        self._readiness_checker = NodeReadinessChecker(diagram, self._tracker)
        
        ExecutionStatePersistence.load_from_state(
            execution_state, 
            self._node_states, 
            self._tracker
        )
        
        self._initialize_node_states()
    
    def _initialize_node_states(self) -> None:
        for node in self.diagram.nodes:
            if node.id not in self._node_states:
                self._node_states[node.id] = NodeState(
                    status=NodeExecutionStatus.PENDING
                )
    
    
    def get_ready_nodes(self) -> list["ExecutableNode"]:
        return [
            node for node in self.diagram.nodes
            if self._readiness_checker.is_node_ready(node, self._node_states)
        ]
    
    def is_complete(self) -> bool:
        if any(state.status == NodeExecutionStatus.RUNNING for state in self._node_states.values()):
            return False
        return len(self.get_ready_nodes()) == 0
    
    def get_variables(self) -> dict[str, Any]:
        return self._variables.copy()
    
    
    def get_node_state(self, node_id: NodeID) -> Optional[NodeState]:
        return self._node_states.get(node_id)
    
    def set_node_state(self, node_id: NodeID, state: NodeState) -> None:
        self._node_states[node_id] = state
    
    def get_node_result(self, node_id: NodeID) -> Optional[dict[str, Any]]:
        protocol_output = self._tracker.get_last_output(node_id)
        if protocol_output:
            result = {"value": protocol_output.value}
            if hasattr(protocol_output, 'metadata') and protocol_output.metadata:
                result["metadata"] = protocol_output.metadata
            return result
        return None
    
    def get_completed_nodes(self) -> list[NodeID]:
        return [
            node_id for node_id, state in self._node_states.items()
            if state.status == NodeExecutionStatus.COMPLETED
        ]
    
    def get_node_execution_count(self, node_id: NodeID) -> int:
        return self._tracker.get_execution_count(node_id)
    
    
    def get_service(self, service_key: Union[str, "ServiceKey"]) -> Any:
        from dipeo.application.unified_service_registry import ServiceKey
        
        if isinstance(service_key, ServiceKey):
            return self._service_registry.get(service_key.name)
        return self._service_registry.get(service_key)
    
    @property
    def service_registry(self) -> "ServiceRegistry":
        return self._service_registry
    
    
    def resolve_inputs(self, node: "ExecutableNode") -> dict[str, Any]:
        from dipeo.application.execution.resolution import (
            TypedInputResolutionService,
        )
        from dipeo.diagram_generated.generated_nodes import PersonJobNode
        
        typed_input_service = TypedInputResolutionService()
        
        node_memory_config = None
        if isinstance(node, PersonJobNode) and node.memory_settings:
            node_memory_config = node.memory_settings
        
        node_outputs_dict = {}
        for n in self.diagram.nodes:
            protocol_output = self._tracker.get_last_output(n.id)
            if protocol_output:
                node_outputs_dict[str(n.id)] = protocol_output
        
        return typed_input_service.resolve_inputs_for_node(
            node_id=str(node.id),
            node_type=node.type,
            diagram=self.diagram,
            node_outputs=node_outputs_dict,
            node_exec_counts={
                str(node_id): self._tracker.get_execution_count(node_id) 
                for node_id in self._node_states.keys()
            },
            node_memory_config=node_memory_config
        )
    
    
    def to_execution_state(self) -> ExecutionState:
        return ExecutionStatePersistence.save_to_state(
            self._execution_id,
            self._diagram_id,
            self.diagram,
            self._node_states,
            self._tracker
        )
    
    
    def get_node(self, node_id: NodeID) -> Optional["ExecutableNode"]:
        return self.diagram.get_node(node_id)
    
    def get_node_output(self, node_id: str) -> Any:
        protocol_output = self._tracker.get_last_output(NodeID(node_id))
        return protocol_output.value if protocol_output else None
    
    def get_execution_summary(self) -> dict[str, Any]:
        return self._tracker.get_execution_summary()
    
    def has_running_nodes(self) -> bool:
        return any(
            state.status == NodeExecutionStatus.RUNNING 
            for state in self._node_states.values()
        )
    
    def count_nodes_by_status(self, statuses: list[str]) -> int:
        status_enums = [NodeExecutionStatus[status] for status in statuses]
        return sum(
            1 for state in self._node_states.values()
            if state.status in status_enums
        )
    
    @property
    def current_node_id(self) -> Optional[NodeID]:
        return self._current_node_id[0]
    
    @property
    def diagram_id(self) -> str:
        return str(self._diagram_id) if self._diagram_id else ""
    
    @property
    def execution_id(self) -> str:
        return str(self._execution_id)
    
    @property
    def container(self) -> Optional["Container"]:
        return self._container
    
    def create_sub_container(self, sub_execution_id: str, config_overrides: Optional[dict] = None) -> Optional["Container"]:
        if self._container is None:
            return None
            
        return self._container.create_sub_container(
            parent_execution_id=self.execution_id,
            sub_execution_id=sub_execution_id,
            config_overrides=config_overrides or {}
        )