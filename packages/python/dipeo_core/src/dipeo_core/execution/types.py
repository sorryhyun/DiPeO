"""Core execution types for DiPeO."""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, Type

from pydantic import BaseModel


class NodeHandler(Protocol):

    async def __call__(
        self,
        props: BaseModel,
        context: "RuntimeContext",
        inputs: Dict[str, Any],
        services: Dict[str, Any],
    ) -> Any:
        ...


@dataclass
class RuntimeContext:

    # Core execution data
    execution_id: str
    current_node_id: str

    # Diagram structure
    edges: List[Dict[str, Any]]
    nodes: List[Dict[str, Any]] = field(default_factory=list)

    # Execution state
    results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    outputs: Dict[str, Any] = field(default_factory=dict)
    exec_cnt: Dict[str, int] = field(default_factory=dict)  # Node execution counts

    # Configuration
    variables: Dict[str, Any] = field(default_factory=dict)
    persons: Dict[str, Any] = field(default_factory=dict)
    api_keys: Dict[str, str] = field(default_factory=dict)

    # Optional metadata
    diagram_id: Optional[str] = None

    def get_node_execution_count(self, node_id: str) -> int:
        return self.exec_cnt.get(node_id, 0)

    def increment_node_execution_count(self, node_id: str) -> None:
        self.exec_cnt[node_id] = self.exec_cnt.get(node_id, 0) + 1

    def get_node_output(self, node_id: str) -> Any:
        return self.outputs.get(node_id)

    def set_node_output(self, node_id: str, output: Any) -> None:
        self.outputs[node_id] = output

    def get_variable(self, name: str, default: Any = None) -> Any:
        return self.variables.get(name, default)

    def set_variable(self, name: str, value: Any) -> None:
        self.variables[name] = value


@dataclass
class ExecutionContext:

    execution_id: str
    diagram_id: str
    node_states: Dict[str, Any] = field(default_factory=dict)
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)

    # Additional fields that might be needed
    edges: List[Dict[str, Any]] = field(default_factory=list)
    results: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    exec_cnt: Dict[str, int] = field(default_factory=dict)
    persons: Dict[str, Any] = field(default_factory=dict)
    api_keys: Dict[str, str] = field(default_factory=dict)

    # Optional current node for runtime context conversion
    current_node_id: str = ""

    def get_node_output(self, node_id: str) -> Any:
        return self.node_outputs.get(node_id)

    def set_node_output(self, node_id: str, output: Any) -> None:
        self.node_outputs[node_id] = output

    def increment_exec_count(self, node_id: str) -> int:
        self.exec_cnt[node_id] = self.exec_cnt.get(node_id, 0) + 1
        return self.exec_cnt[node_id]

    def get_conversation_history(self, person_id: str) -> List[Dict[str, Any]]:
        return self.persons.get(person_id, [])

    def add_to_conversation(self, person_id: str, message: Dict[str, Any]) -> None:
        if person_id not in self.persons:
            self.persons[person_id] = []
        self.persons[person_id].append(message)

    def get_api_key(self, service: str) -> Optional[str]:
        return self.api_keys.get(service)

    def to_runtime_context(self) -> "RuntimeContext":
        return RuntimeContext(
            execution_id=self.execution_id,
            current_node_id=self.current_node_id,
            edges=self.edges,
            nodes=[],  # Nodes list is typically populated separately
            results=self.results,
            outputs=self.node_outputs,
            exec_cnt=self.exec_cnt,
            variables=self.variables,
            persons=self.persons,
            api_keys=self.api_keys,
            diagram_id=self.diagram_id,
        )


@dataclass
class NodeDefinition:

    type: str
    node_schema: Type[BaseModel]  # Renamed from 'schema' to avoid Pydantic conflict
    handler: NodeHandler
    requires_services: List[str] = field(default_factory=list)
    description: str = ""


@dataclass
class ExecutionOptions:

    debug: bool = False
    timeout: Optional[float] = None
    max_iterations: Optional[int] = None
    monitor: bool = False
    interactive: bool = False
    variables: Dict[str, Any] = field(default_factory=dict)


# Conversion utilities
def runtime_to_execution_context(
    runtime_ctx: RuntimeContext, diagram_id: Optional[str] = None
) -> ExecutionContext:
    return ExecutionContext(
        execution_id=runtime_ctx.execution_id,
        diagram_id=diagram_id or runtime_ctx.diagram_id or "",
        node_states={},  # Can be populated if needed
        node_outputs=runtime_ctx.outputs,
        variables=runtime_ctx.variables,
        edges=runtime_ctx.edges,
        results=runtime_ctx.results,
        exec_cnt=runtime_ctx.exec_cnt,
        persons=runtime_ctx.persons,
        api_keys=runtime_ctx.api_keys,
    )


def execution_to_runtime_context(
    exec_ctx: ExecutionContext, current_node_id: str = ""
) -> RuntimeContext:
    return RuntimeContext(
        execution_id=exec_ctx.execution_id,
        current_node_id=current_node_id,
        edges=exec_ctx.edges,
        results=exec_ctx.results,
        outputs=exec_ctx.node_outputs,
        exec_cnt=exec_ctx.exec_cnt,
        variables=exec_ctx.variables,
        persons=exec_ctx.persons,
        api_keys=exec_ctx.api_keys,
        diagram_id=exec_ctx.diagram_id,
    )
