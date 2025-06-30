from dataclasses import dataclass, field
from typing import Any

from dipeo_core import ExecutionContext as CoreExecutionContext
from dipeo_core import RuntimeContext
from dipeo_domain.models import DomainArrow, NodeOutput, TokenUsage


@dataclass
class ExecutionContext(CoreExecutionContext):
    """Server-specific execution context extending the core ExecutionContext.

    This adds server-specific functionality while maintaining compatibility
    with the core ExecutionContext used throughout the system.
    """

    # Additional server-specific fields
    nodes: list[Any] = field(default_factory=list)  # DomainNode list
    edges: list[DomainArrow] = field(default_factory=list)

    # Token usage accumulation
    _token_accumulator: dict[str, TokenUsage] = field(default_factory=dict, init=False)

    def get_node_output(self, node_id: str) -> NodeOutput | None:
        """Override to handle NodeOutput type specifically."""
        output = super().get_node_output(node_id)
        if isinstance(output, NodeOutput):
            return output
        return None

    def set_node_output(self, node_id: str, output: NodeOutput) -> None:
        """Override to handle NodeOutput type specifically."""
        super().set_node_output(node_id, output)

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
            exec_cnt=self.exec_cnt,
            variables=self.variables,
            persons=self.persons,
            api_keys=self.api_keys,
            diagram_id=self.diagram_id,
        )
