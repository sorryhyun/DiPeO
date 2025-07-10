"""Execution order calculation using topological sort."""

from typing import List, Dict, Set, Tuple, Optional
from collections import deque
from dataclasses import dataclass

from dipeo.models import NodeID, NodeType, DomainNode
from dipeo.core.static import ExecutableEdge


@dataclass
class ExecutionGroup:
    """A group of nodes that can be executed in parallel."""
    level: int
    nodes: List[NodeID]


class CycleDetectedError(Exception):
    """Raised when a cycle is detected in the diagram."""
    def __init__(self, cycle_nodes: Set[NodeID]):
        self.cycle_nodes = cycle_nodes
        super().__init__(f"Cycle detected involving nodes: {cycle_nodes}")


class ExecutionOrderCalculator:
    """Calculates the execution order for diagram nodes using topological sort.
    
    This class determines the order in which nodes should be executed,
    ensuring that all dependencies are satisfied. It also identifies
    nodes that can be executed in parallel.
    """
    
    def __init__(self):
        """Initialize the ExecutionOrderCalculator."""
        self._errors: List[str] = []
    
    def calculate_order(
        self,
        nodes: List[DomainNode],
        edges: List[ExecutableEdge]
    ) -> Tuple[List[NodeID], List[ExecutionGroup], List[str]]:
        """Calculate the execution order for nodes.
        
        Args:
            nodes: List of nodes in the diagram
            edges: List of edges representing dependencies
            
        Returns:
            Tuple of (execution order, parallel groups, errors)
        """
        self._errors = []
        
        # Build adjacency lists
        graph, in_degree = self._build_graph(nodes, edges)
        
        # Detect cycles
        try:
            self._detect_cycles(graph, {node.id for node in nodes})
        except CycleDetectedError as e:
            # For now, treat cycles as warnings for iterative diagrams
            # In the future, we might want to handle iterative nodes specially
            self._errors.append(f"Warning: {str(e)} - Using best-effort topological ordering")
            # Continue with best-effort ordering instead of failing
        
        # Perform topological sort with level tracking
        order, groups = self._topological_sort_with_levels(nodes, graph, in_degree)
        
        # Validate the result
        if len(order) != len(nodes):
            unreachable = {node.id for node in nodes} - set(order)
            if unreachable:
                self._errors.append(f"Unreachable nodes detected: {unreachable}")
        
        return order, groups, self._errors
    
    def _build_graph(
        self,
        nodes: List[DomainNode],
        edges: List[ExecutableEdge]
    ) -> Tuple[Dict[NodeID, List[NodeID]], Dict[NodeID, int]]:
        """Build adjacency list and in-degree map from edges.
        
        Args:
            nodes: List of nodes
            edges: List of edges
            
        Returns:
            Tuple of (adjacency list, in-degree map)
        """
        graph: Dict[NodeID, List[NodeID]] = {node.id: [] for node in nodes}
        in_degree: Dict[NodeID, int] = {node.id: 0 for node in nodes}
        
        for edge in edges:
            if edge.source_node_id in graph:
                graph[edge.source_node_id].append(edge.target_node_id)
            if edge.target_node_id in in_degree:
                in_degree[edge.target_node_id] += 1
        
        return graph, in_degree
    
    def _detect_cycles(
        self,
        graph: Dict[NodeID, List[NodeID]],
        node_ids: Set[NodeID]
    ) -> None:
        """Detect cycles in the graph using DFS.
        
        Args:
            graph: Adjacency list representation
            node_ids: Set of all node IDs
            
        Raises:
            CycleDetectedError: If a cycle is found
        """
        WHITE = 0  # Not visited
        GRAY = 1   # Currently visiting
        BLACK = 2  # Visited
        
        colors = {node_id: WHITE for node_id in node_ids}
        cycle_nodes: Set[NodeID] = set()
        
        def dfs(node: NodeID, path: List[NodeID]) -> bool:
            """DFS helper to detect cycles."""
            colors[node] = GRAY
            path.append(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in colors:
                    continue
                    
                if colors[neighbor] == GRAY:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle_nodes.update(path[cycle_start:])
                    return True
                elif colors[neighbor] == WHITE:
                    if dfs(neighbor, path):
                        return True
            
            path.pop()
            colors[node] = BLACK
            return False
        
        # Check each unvisited node
        for node_id in node_ids:
            if colors[node_id] == WHITE:
                if dfs(node_id, []):
                    raise CycleDetectedError(cycle_nodes)
    
    def _topological_sort_with_levels(
        self,
        nodes: List[DomainNode],
        graph: Dict[NodeID, List[NodeID]],
        in_degree: Dict[NodeID, int]
    ) -> Tuple[List[NodeID], List[ExecutionGroup]]:
        """Perform topological sort tracking execution levels.
        
        Args:
            nodes: List of nodes
            graph: Adjacency list
            in_degree: In-degree map
            
        Returns:
            Tuple of (execution order, parallel groups)
        """
        # Find all nodes with no dependencies (including start nodes)
        queue = deque()
        for node in nodes:
            if in_degree[node.id] == 0:
                queue.append(node.id)
        
        order: List[NodeID] = []
        groups: List[ExecutionGroup] = []
        level = 0
        
        while queue:
            # Process all nodes at current level
            level_size = len(queue)
            level_nodes: List[NodeID] = []
            
            for _ in range(level_size):
                node_id = queue.popleft()
                order.append(node_id)
                level_nodes.append(node_id)
                
                # Update neighbors
                for neighbor in graph.get(node_id, []):
                    if neighbor in in_degree:
                        in_degree[neighbor] -= 1
                        if in_degree[neighbor] == 0:
                            queue.append(neighbor)
            
            # Add this level as a parallel execution group
            if level_nodes:
                groups.append(ExecutionGroup(level=level, nodes=level_nodes))
                level += 1
        
        return order, groups
    
    def optimize_for_parallelism(
        self,
        groups: List[ExecutionGroup],
        nodes: Dict[NodeID, DomainNode]
    ) -> List[ExecutionGroup]:
        """Optimize execution groups for maximum parallelism.
        
        Args:
            groups: Initial execution groups
            nodes: Node lookup dictionary
            
        Returns:
            Optimized execution groups
        """
        optimized_groups = []
        
        for group in groups:
            # Split heavy computation nodes into separate sub-groups
            # to avoid blocking lighter nodes
            heavy_nodes = []
            light_nodes = []
            
            for node_id in group.nodes:
                node = nodes.get(node_id)
                if node and self._is_heavy_node(node):
                    heavy_nodes.append(node_id)
                else:
                    light_nodes.append(node_id)
            
            # Add light nodes first for better responsiveness
            if light_nodes:
                optimized_groups.append(
                    ExecutionGroup(level=group.level, nodes=light_nodes)
                )
            if heavy_nodes:
                optimized_groups.append(
                    ExecutionGroup(level=group.level, nodes=heavy_nodes)
                )
        
        return optimized_groups
    
    def _is_heavy_node(self, node: DomainNode) -> bool:
        """Determine if a node is computationally heavy.
        
        Args:
            node: The node to check
            
        Returns:
            True if the node is likely to be slow
        """
        # Person nodes (LLM calls) are typically slow
        if node.type == NodeType.person_job:
            return True
        
        # Job nodes might be slow depending on the task
        if node.type == NodeType.job:
            # Could inspect node.data for hints about complexity
            return True
        
        # Database operations can be slow
        if node.type == NodeType.db:
            return True
        
        # Conditions, hooks, and other nodes are typically fast
        return False