from dataclasses import dataclass
from typing import Any

from dipeo_core.unified_context import UnifiedExecutionContext
from dipeo_core.execution.types import RuntimeContext as LegacyRuntimeContext
from dipeo_domain.handle_utils import parse_handle_id, extract_node_id_from_handle


@dataclass
class ExecutionContext(UnifiedExecutionContext):
    """Server-specific execution context extending the unified execution context.

    This adds server-specific functionality while maintaining compatibility
    with the UnifiedExecutionContext used throughout the system.
    """

    def find_edges_from(self, node_id: str) -> list[Any]:
        """Find edges originating from a node."""
        from dipeo_domain.models import DomainArrow
        # Parse handle IDs to extract node IDs (format: nodeId_handleName_direction)
        result = []
        for edge in self.edges:
            if hasattr(edge, 'source') and edge.source:
                # Extract node ID from handle
                edge_node_id = extract_node_id_from_handle(edge.source)
                if edge_node_id == node_id:
                    result.append(edge)
        return result

    def find_edges_to(self, node_id: str) -> list[Any]:
        """Find edges targeting a node."""
        from dipeo_domain.models import DomainArrow
        # Parse handle IDs to extract node IDs (format: nodeId_handleName_direction)
        result = []
        for edge in self.edges:
            if hasattr(edge, 'target') and edge.target:
                # Extract node ID from handle
                edge_node_id = extract_node_id_from_handle(edge.target)
                if edge_node_id == node_id:
                    result.append(edge)
        return result

    def to_runtime_context(self, current_node_id: str = "", node_view: Any | None = None) -> LegacyRuntimeContext:
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

        # Convert nodes to dict format from diagram
        nodes = []
        for node in self.diagram.nodes:
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

        # Extract persons from diagram
        persons = {}
        if self.diagram.persons:
            for person in self.diagram.persons:
                if hasattr(person, "model_dump"):
                    persons[person.id] = person.model_dump()
                else:
                    persons[person.id] = person

        return LegacyRuntimeContext(
            execution_id=self.execution_id,
            current_node_id=current_node_id,
            edges=edges,
            nodes=nodes,
            results={},  # Not used in current handlers
            outputs=outputs,
            exec_cnt=self.exec_counts,
            variables=self.variables,
            persons=persons,
            api_keys=self.api_keys,
            diagram_id=self.diagram.id,
        )
