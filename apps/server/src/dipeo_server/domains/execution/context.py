from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from dipeo_domain.models import DomainArrow, DomainDiagram, NodeOutput, TokenUsage

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
    conversation_service: Optional[Any] = field(default=None)
    notion_service: Optional[Any] = field(default=None)
    state_store: StateRegistry = field(default=None)
    interactive_handler: Optional[Callable] = field(default=None)
    stream_callback: Optional[Callable] = field(default=None)
    
    # Token usage accumulation
    _token_accumulator: Dict[str, TokenUsage] = field(default_factory=dict, init=False)

    def get_node_output(self, node_id: str) -> Optional[NodeOutput]:
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

    def get_api_key(self, service: str) -> Optional[str]:
        return self.api_keys.get(service)

    def find_edges_from(self, node_id: str) -> List[DomainArrow]:
        return [edge for edge in self.edges if edge.source.split(":")[0] == node_id]

    def find_edges_to(self, node_id: str) -> List[DomainArrow]:
        return [edge for edge in self.edges if edge.target.split(":")[0] == node_id]
    
    def add_token_usage(self, node_id: str, tokens: TokenUsage) -> None:
        """Accumulate token usage in memory for later persistence."""
        self._token_accumulator[node_id] = tokens
    
    def get_total_token_usage(self) -> TokenUsage:
        """Calculate total token usage from accumulator."""
        if not self._token_accumulator:
            return TokenUsage(input=0, output=0, total=0)
        
        total = TokenUsage(input=0, output=0, total=0)
        for tokens in self._token_accumulator.values():
            total.input += tokens.input
            total.output += tokens.output
            total.total += tokens.total
            if tokens.cached:
                total.cached = (total.cached or 0) + tokens.cached
        return total
