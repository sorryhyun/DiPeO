"""Optimization phase for diagram compilation."""

from dipeo.diagram_generated import NodeID, NodeType

from ...validation.utils import find_unreachable_nodes
from ..types import CompilationPhase
from .base import CompilationContext, PhaseInterface


class OptimizationPhase(PhaseInterface):
    """Phase 5: Analyze and optimize the execution graph."""

    @property
    def phase_type(self) -> CompilationPhase:
        return CompilationPhase.OPTIMIZATION

    def execute(self, context: CompilationContext) -> None:
        """Perform optimization analysis and emit warnings."""
        self._detect_unreachable_nodes(context)
        self._detect_cycles(context)
        self._analyze_parallel_execution(context)

    def _detect_unreachable_nodes(self, context: CompilationContext) -> None:
        """Detect and warn about unreachable nodes."""
        unreachable = find_unreachable_nodes(context.nodes_list, context.arrows_list)

        for node_id in unreachable:
            node = next((n for n in context.typed_nodes if n.id == node_id), None)
            if node and node.type != NodeType.START:
                context.result.add_warning(
                    self.phase_type,
                    f"Node '{node.id}' is unreachable from any start node",
                    node_id=node.id,
                    suggestion="Add a connection from a reachable node or start node",
                )

    def _detect_cycles(self, context: CompilationContext) -> None:
        """Detect and warn about circular dependencies."""
        cycles = self._find_cycles(context.node_dependencies)
        if cycles:
            context.result.add_warning(
                self.phase_type,
                f"Circular dependencies detected: {cycles}",
                suggestion="Consider using condition nodes to break cycles",
            )

    def _analyze_parallel_execution(self, context: CompilationContext) -> None:
        """Analyze potential parallel execution opportunities."""
        parallel_groups = self._find_parallel_groups(context.start_nodes, context.node_dependencies)
        if parallel_groups:
            context.result.metadata["parallel_groups"] = parallel_groups

    def _find_cycles(self, dependencies: dict[NodeID, set[NodeID]]) -> list[list[NodeID]]:
        """Find all cycles in the dependency graph.

        Args:
            dependencies: Mapping of node to its dependencies

        Returns:
            List of cycles, where each cycle is a list of node IDs
        """
        cycles = []

        def has_path(start: NodeID, end: NodeID, visited: set[NodeID]) -> bool:
            if start == end and visited:
                return True
            if start in visited:
                return False

            visited.add(start)
            return any(has_path(dep, end, visited.copy()) for dep in dependencies.get(start, set()))

        for node in dependencies:
            if has_path(node, node, set()):
                cycles.append([node])

        return cycles

    def _find_parallel_groups(
        self, start_nodes: set[NodeID], dependencies: dict[NodeID, set[NodeID]]
    ) -> list[set[NodeID]]:
        """Find groups of nodes that can be executed in parallel.

        Args:
            start_nodes: Set of start node IDs
            dependencies: Mapping of node to its dependencies

        Returns:
            List of node sets that can execute in parallel
        """
        parallel_groups = []
        # TODO: Implement parallel execution analysis
        return parallel_groups
