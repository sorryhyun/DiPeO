from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from dipeo_domain.models import DomainArrow, DomainDiagram, NodeOutput

from dipeo_server.domains.llm.services import LLMService
from dipeo_server.infrastructure.persistence import FileService, StateRegistry


@dataclass
class ExecutionContext:
    diagram: DomainDiagram
    edges: List[DomainArrow]
    node_outputs: Dict[str, NodeOutput] = field(default_factory=dict)
    current_node_id: str = ""
    execution_id: str = ""
    exec_counts: Dict[str, int] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    persons: Dict[str, Any] = field(default_factory=dict)
    api_keys: Dict[str, str] = field(default_factory=dict)

    llm_service: LLMService = field(default=None)
    file_service: FileService = field(default=None)
    memory_service: Optional[Any] = field(default=None)
    notion_service: Optional[Any] = field(default=None)
    state_store: StateRegistry = field(default=None)
    interactive_handler: Optional[Callable] = field(default=None)
    stream_callback: Optional[Callable] = field(default=None)

    def get_node_output(self, node_id: str) -> NodeOutput | None:
        return self.node_outputs.get(node_id)

    def set_node_output(self, node_id: str, output: NodeOutput) -> None:
        self.node_outputs[node_id] = output

    def increment_exec_count(self, node_id: str) -> int:
        self.exec_counts[node_id] = self.exec_counts.get(node_id, 0) + 1
        return self.exec_counts[node_id]

    def get_conversation_history(self, person_id: str) -> List[Dict[str, Any]]:
        return self.persons.get(person_id, [])

    def add_to_conversation(self, person_id: str, message: Dict[str, Any]) -> None:
        if person_id not in self.persons:
            self.persons[person_id] = []
        self.persons[person_id].append(message)

    def get_api_key(self, service: str) -> str | None:
        return self.api_keys.get(service)

    def find_edges_from(self, node_id: str) -> List[DomainArrow]:
        return [edge for edge in self.edges if edge.source.split(":")[0] == node_id]

    def find_edges_to(self, node_id: str) -> List[DomainArrow]:
        return [edge for edge in self.edges if edge.target.split(":")[0] == node_id]
