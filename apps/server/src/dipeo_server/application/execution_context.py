from dataclasses import dataclass, field
from typing import Any

from dipeo_core import RuntimeContext
from dipeo_domain.models import DomainArrow, NodeOutput, TokenUsage


@dataclass
class ExecutionContext:
    """Pure data container for execution state - no service dependencies."""

    # Core execution data
    execution_id: str
    diagram_id: str

    # State
    node_outputs: dict[str, NodeOutput] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    exec_counts: dict[str, int] = field(default_factory=dict)
    current_node_id: str = ""

    # Structure (for handlers that need it)
    nodes: list[Any] = field(default_factory=list)  # DomainNode list
    edges: list[DomainArrow] = field(default_factory=list)
    persons: dict[str, Any] = field(default_factory=dict)  # Person configurations

    # API keys (needed for some operations)
    api_keys: dict[str, str] = field(default_factory=dict)

    # Token usage accumulation
    _token_accumulator: dict[str, TokenUsage] = field(default_factory=dict, init=False)

    def get_node_output(self, node_id: str) -> NodeOutput | None:
        return self.node_outputs.get(node_id)

    def set_node_output(self, node_id: str, output: NodeOutput) -> None:
        self.node_outputs[node_id] = output

    def increment_exec_count(self, node_id: str) -> int:
        self.exec_counts[node_id] = self.exec_counts.get(node_id, 0) + 1
        return self.exec_counts[node_id]

    def get_conversation_history(self, person_id: str) -> list[dict[str, Any]]:
        return self.persons.get(person_id, [])

    def add_to_conversation(self, person_id: str, message: dict[str, Any]) -> None:
        if person_id not in self.persons:
            self.persons[person_id] = []
        self.persons[person_id].append(message)

    def get_api_key(self, service: str) -> str | None:
        return self.api_keys.get(service)

    def find_edges_from(self, node_id: str) -> list[DomainArrow]:
        return [edge for edge in self.edges if edge.source.split(":")[0] == node_id]

    def find_edges_to(self, node_id: str) -> list[DomainArrow]:
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

    def to_runtime_context(self, node_view: Any | None = None) -> RuntimeContext:
        """Convert ExecutionContext to RuntimeContext for BaseNodeHandler compatibility."""
        # Convert edges to dict format
        edges = [
            {
                "source": edge.source,
                "target": edge.target,
                "data": edge.data,
            }
            for edge in self.edges
        ]

        # Convert nodes to dict format if they are domain objects
        nodes = []
        for node in self.nodes:
            if hasattr(node, "model_dump"):
                nodes.append(node.model_dump())
            else:
                nodes.append(node)

        # Get current outputs from node_view if available
        outputs = {}
        if node_view and hasattr(node_view, "node_views"):
            # Collect outputs from completed nodes
            for node_id, view in node_view.node_views.items():
                if view.output:
                    outputs[node_id] = view.output.value
        else:
            # Use stored outputs
            outputs = {k: v.value for k, v in self.node_outputs.items() if v}

        return RuntimeContext(
            execution_id=self.execution_id,
            current_node_id=self.current_node_id,
            edges=edges,
            nodes=nodes,
            results={},  # Not used in current handlers
            outputs=outputs,
            exec_cnt=self.exec_counts,
            variables=self.variables,
            persons=self.persons,
            api_keys=self.api_keys,
            diagram_id=self.diagram_id,
        )
