"""Dependency tracking for node scheduling."""

from collections import defaultdict
from typing import TYPE_CHECKING

from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated import NodeID, NodeType
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram

if TYPE_CHECKING:
    pass

logger = get_module_logger(__name__)


class DependencyTracker:
    """Manages dependency graph with indegree tracking and priority dependencies."""

    def __init__(self, diagram: ExecutableDiagram):
        self.diagram = diagram
        self._indegree: dict[NodeID, int] = {}
        self._dependents: dict[NodeID, set[NodeID]] = defaultdict(set)
        self._priority_dependencies: dict[NodeID, set[NodeID]] = defaultdict(set)
        self._processed_nodes: set[NodeID] = set()

        self._initialize_dependencies()

    def _is_conditional_edge(self, edge) -> bool:
        """Check if an edge is conditional."""
        if getattr(edge, "is_conditional", False):
            return True
        return str(getattr(edge, "source_output", "")).lower() in ("condtrue", "condfalse")

    def _initialize_dependencies(self) -> None:
        """Initialize dependency graph with indegree and dependents."""
        all_nodes = self.diagram.get_nodes_by_type(None) or self.diagram.nodes
        for node in all_nodes:
            self._indegree[node.id] = 0

        nodes_with_non_conditional_deps: set[NodeID] = set()
        incoming_by_target: dict[NodeID, list] = defaultdict(list)
        edges_by_source: dict[NodeID, list] = defaultdict(list)
        all_edges = []
        for node in all_nodes:
            for edge in self.diagram.get_outgoing_edges(node.id):
                edges_by_source[edge.source_node_id].append(edge)
                incoming_by_target[edge.target_node_id].append(edge)
                all_edges.append(edge)

        for edge in all_edges:
            source_node = next((n for n in all_nodes if n.id == edge.source_node_id), None)
            if (
                source_node
                and hasattr(source_node, "type")
                and source_node.type == NodeType.CONDITION
                and getattr(source_node, "skippable", False)
            ):
                target_incoming_edges = incoming_by_target.get(edge.target_node_id, [])
                unique_sources = set(e.source_node_id for e in target_incoming_edges)

                if len(unique_sources) > 1:
                    continue

            if self._is_conditional_edge(edge):
                continue

            self._indegree[edge.target_node_id] += 1
            self._dependents[edge.source_node_id].add(edge.target_node_id)
            nodes_with_non_conditional_deps.add(edge.target_node_id)

        for _source_id, edges in edges_by_source.items():
            sorted_edges = sorted(edges, key=lambda e: -getattr(e, "execution_priority", 0))

            for i, lower_edge in enumerate(sorted_edges):
                for higher_edge in sorted_edges[:i]:
                    if getattr(higher_edge, "execution_priority", 0) > getattr(
                        lower_edge, "execution_priority", 0
                    ):
                        self._priority_dependencies[lower_edge.target_node_id].add(
                            higher_edge.target_node_id
                        )

    def get_initial_ready_nodes(self) -> set[NodeID]:
        """Get nodes with zero indegree that are ready to execute."""
        return {node_id for node_id, count in self._indegree.items() if count == 0}

    def mark_node_completed(self, node_id: NodeID) -> set[NodeID]:
        """Mark a node as completed and return newly ready nodes."""
        if node_id in self._processed_nodes:
            return set()

        self._processed_nodes.add(node_id)
        newly_ready = set()

        for dependent_id in self._dependents.get(node_id, set()):
            self._indegree[dependent_id] -= 1
            if self._indegree[dependent_id] == 0:
                newly_ready.add(dependent_id)

        return newly_ready

    def get_indegree(self, node_id: NodeID) -> int:
        """Get the current indegree for a node."""
        return self._indegree.get(node_id, 0)

    def get_dependents(self, node_id: NodeID) -> set[NodeID]:
        """Get all nodes that depend on this node."""
        return self._dependents.get(node_id, set())

    def get_priority_dependencies(self, node_id: NodeID) -> set[NodeID]:
        """Get higher-priority nodes that must complete first."""
        return self._priority_dependencies.get(node_id, set())

    def get_stats(self) -> dict:
        """Get dependency tracking statistics."""
        all_nodes_list = self.diagram.get_nodes_by_type(None) or self.diagram.nodes
        all_nodes = {node.id for node in all_nodes_list}
        pending_count = len(all_nodes - self._processed_nodes)
        return {
            "total_nodes": len(all_nodes_list),
            "processed_nodes": len(self._processed_nodes),
            "pending_nodes": pending_count,
            "nodes_with_dependencies": sum(1 for c in self._indegree.values() if c > 0),
        }
