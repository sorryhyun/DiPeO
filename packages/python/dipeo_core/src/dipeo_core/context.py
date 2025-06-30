"""Execution context for DiPeO.

This module provides ExecutionContext which is the main context object used during
diagram execution. It's a simplified version that domain services can use without
depending on application-specific implementations.
"""

from dataclasses import dataclass, field
from typing import Any, Callable

from dipeo_domain.models import DomainArrow, DomainDiagram, NodeOutput, TokenUsage

from .execution.types import RuntimeContext


@dataclass
class ExecutionContext:
    """Pure data container for execution state.
    
    This context is used by the execution engine and domain services to track
    the state of diagram execution without service dependencies.
    """

    # Core execution data
    execution_id: str
    diagram: DomainDiagram  # The diagram being executed
    
    # Structure
    edges: list[DomainArrow] = field(default_factory=list)
    
    # State tracking
    node_outputs: dict[str, NodeOutput] = field(default_factory=dict)
    variables: dict[str, Any] = field(default_factory=dict)
    exec_counts: dict[str, int] = field(default_factory=dict)
    
    # API keys (needed for LLM operations)
    api_keys: dict[str, str] = field(default_factory=dict)
    
    # Services (injected during execution)
    llm_service: Any | None = None
    file_service: Any | None = None
    notion_service: Any | None = None
    conversation_service: Any | None = None
    api_key_service: Any | None = None
    state_store: Any | None = None
    
    # Execution options
    interactive_handler: Callable | None = None
    stream_callback: Callable | None = None
    
    # Token usage tracking
    _token_accumulator: dict[str, TokenUsage] = field(default_factory=dict, init=False)
    
    # Execution view (for view-based engine)
    _execution_view: Any | None = field(default=None, init=False)

    def get_node_output(self, node_id: str) -> NodeOutput | None:
        return self.node_outputs.get(node_id)

    def set_node_output(self, node_id: str, output: NodeOutput) -> None:
        self.node_outputs[node_id] = output

    def increment_exec_count(self, node_id: str) -> int:
        """Increment and return the execution count for a node."""
        self.exec_counts[node_id] = self.exec_counts.get(node_id, 0) + 1
        return self.exec_counts[node_id]

    def get_api_key(self, service: str) -> str | None:
        return self.api_keys.get(service)

    def add_token_usage(self, node_id: str, tokens: TokenUsage) -> None:
        """Accumulate token usage for later tracking."""
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

    def to_runtime_context(self, current_node_id: str = "") -> RuntimeContext:
        """Convert to RuntimeContext for handler compatibility."""
        # Convert edges to dict format
        edges = [
            {
                "source": edge.source,
                "target": edge.target,
                "data": edge.data,
            }
            for edge in self.edges
        ]
        
        # Convert nodes to dict format
        nodes = []
        for node in self.diagram.nodes:
            if hasattr(node, "model_dump"):
                nodes.append(node.model_dump())
            else:
                nodes.append(node)
        
        # Extract outputs
        outputs = {k: v.value for k, v in self.node_outputs.items() if v}
        
        # Extract persons to dict format
        persons = {}
        if self.diagram.persons:
            for person in self.diagram.persons:
                if hasattr(person, "model_dump"):
                    persons[person.id] = person.model_dump()
                else:
                    persons[person.id] = person

        return RuntimeContext(
            execution_id=self.execution_id,
            current_node_id=current_node_id,
            edges=edges,
            nodes=nodes,
            results={},  # Legacy field
            outputs=outputs,
            exec_cnt=self.exec_counts,
            variables=self.variables,
            persons=persons,
            api_keys=self.api_keys,
            diagram_id=self.diagram.id,
        )