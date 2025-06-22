from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from dipeo_domain.models import DomainArrow, DomainDiagram, NodeOutput

from dipeo_server.core.services import FileService
from dipeo_server.domains.llm.services import LLMService
from dipeo_server.domains.execution.services.state_store import StateStore


@dataclass
class ExecutionContext:
    """Single context used throughout the system."""

    # Core execution data
    diagram: DomainDiagram
    edges: List[DomainArrow]  # Use Arrow objects consistently
    node_outputs: Dict[str, NodeOutput] = field(default_factory=dict)  # Direct storage, no "results" wrapper
    current_node_id: str = ""
    execution_id: str = ""
    exec_counts: Dict[str, int] = field(default_factory=dict)
    variables: Dict[str, Any] = field(default_factory=dict)
    persons: Dict[str, Any] = field(default_factory=dict)  # Conversation history
    api_keys: Dict[str, str] = field(default_factory=dict)

    # Services as direct attributes
    llm_service: LLMService = field(default=None)
    file_service: FileService = field(default=None)
    memory_service: Optional[any] = field(default=None)
    notion_service: Optional[any] = field(default=None)
    state_store: StateStore = field(default=None)
    interactive_handler: Optional[Callable] = field(default=None)
    stream_callback: Optional[Callable] = field(default=None)

    def get_node_output(self, node_id: str) -> NodeOutput | None:
        """Get output for a specific node."""
        return self.node_outputs.get(node_id)

    def set_node_output(self, node_id: str, output: NodeOutput) -> None:
        """Set output for a specific node."""
        self.node_outputs[node_id] = output

    def increment_exec_count(self, node_id: str) -> int:
        """Increment and return execution count for a node."""
        self.exec_counts[node_id] = self.exec_counts.get(node_id, 0) + 1
        return self.exec_counts[node_id]

    def get_conversation_history(self, person_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a person."""
        return self.persons.get(person_id, [])

    def add_to_conversation(self, person_id: str, message: Dict[str, Any]) -> None:
        """Add a message to person's conversation history."""
        if person_id not in self.persons:
            self.persons[person_id] = []
        self.persons[person_id].append(message)

    def get_api_key(self, service: str) -> str | None:
        """Get API key for a service."""
        return self.api_keys.get(service)

    def find_edges_from(self, node_id: str) -> List[DomainArrow]:
        """Find all edges originating from a node."""
        return [edge for edge in self.edges if edge.from_node == node_id]

    def find_edges_to(self, node_id: str) -> List[DomainArrow]:
        """Find all edges pointing to a node."""
        return [edge for edge in self.edges if edge.to_node == node_id]
