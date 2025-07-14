# Execution order calculation using topological sort.

from collections import deque
from dataclasses import dataclass

from dipeo.core.static import ExecutableEdge
from dipeo.models import DomainNode, NodeID, NodeType


@dataclass
class ExecutionGroup:
    level: int
    nodes: list[NodeID]


class CycleDetectedError(Exception):
    def __init__(self, cycle_nodes: set[NodeID]):
        self.cycle_nodes = cycle_nodes
        super().__init__(f"Cycle detected involving nodes: {cycle_nodes}")


class ExecutionOrderCalculator:
    
    def __init__(self):
        self._errors: list[str] = []
        self._warnings: list[str] = []
    
    def calculate_order(
        self,
        nodes: list[DomainNode],
        edges: list[ExecutableEdge]
    ) -> tuple[list[NodeID], list[ExecutionGroup], list[str]]:
        self._errors = []
        self._warnings = []
        
        # Build adjacency lists
        graph, in_degree = self._build_graph(nodes, edges)
        
        # Detect cycles
        try:
            self._detect_cycles(graph, {node.id for node in nodes})
        except CycleDetectedError as e:
            # For iterative diagrams, cycles are expected - treat as warning
            self._warnings.append(f"{e!s} - Using best-effort topological ordering")
            # Continue with best-effort ordering instead of failing
        
        # Perform topological sort with level tracking
        order, groups = self._topological_sort_with_levels(nodes, graph, in_degree)
        
        # Validate the result
        if len(order) != len(nodes):
            unreachable = {node.id for node in nodes} - set(order)
            if unreachable:
                self._errors.append(f"Unreachable nodes detected: {unreachable}")
        
        return order, groups, self._errors
    
    def get_warnings(self) -> list[str]:
        return self._warnings
    
    def _build_graph(
        self,
        nodes: list[DomainNode],
        edges: list[ExecutableEdge]
    ) -> tuple[dict[NodeID, list[NodeID]], dict[NodeID, int]]:
        graph: dict[NodeID, list[NodeID]] = {node.id: [] for node in nodes}
        in_degree: dict[NodeID, int] = {node.id: 0 for node in nodes}
        
        for edge in edges:
            if edge.source_node_id in graph:
                graph[edge.source_node_id].append(edge.target_node_id)
            if edge.target_node_id in in_degree:
                in_degree[edge.target_node_id] += 1
        
        return graph, in_degree
    
    def _detect_cycles(
        self,
        graph: dict[NodeID, list[NodeID]],
        node_ids: set[NodeID]
    ) -> None:
        WHITE = 0  # Not visited
        GRAY = 1   # Currently visiting
        BLACK = 2  # Visited
        
        colors = {node_id: WHITE for node_id in node_ids}
        cycle_nodes: set[NodeID] = set()
        
        def dfs(node: NodeID, path: list[NodeID]) -> bool:
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
        nodes: list[DomainNode],
        graph: dict[NodeID, list[NodeID]],
        in_degree: dict[NodeID, int]
    ) -> tuple[list[NodeID], list[ExecutionGroup]]:
        # Make a copy of in_degree to avoid modifying the original
        in_degree_copy = in_degree.copy()
        
        # Find all nodes with no dependencies (including start nodes)
        queue = deque()
        for node in nodes:
            if in_degree_copy[node.id] == 0:
                queue.append(node.id)
        
        order: list[NodeID] = []
        groups: list[ExecutionGroup] = []
        level = 0
        processed_nodes = set()
        
        while queue:
            # Process all nodes at current level
            level_size = len(queue)
            level_nodes: list[NodeID] = []
            
            for _ in range(level_size):
                node_id = queue.popleft()
                if node_id not in processed_nodes:
                    order.append(node_id)
                    level_nodes.append(node_id)
                    processed_nodes.add(node_id)
                
                # Update neighbors
                for neighbor in graph.get(node_id, []):
                    if neighbor in in_degree_copy:
                        in_degree_copy[neighbor] -= 1
                        if in_degree_copy[neighbor] == 0:
                            queue.append(neighbor)
            
            # Add this level as a parallel execution group
            if level_nodes:
                groups.append(ExecutionGroup(level=level, nodes=level_nodes))
                level += 1
        
        # Handle nodes that are part of cycles (not reached by standard topological sort)
        remaining_nodes = set(node.id for node in nodes) - processed_nodes
        if remaining_nodes:
            # For cyclic nodes, add them in a reasonable order
            # Start with nodes that have the fewest remaining dependencies
            while remaining_nodes:
                # Find node with minimum remaining in-degree
                min_node = None
                min_degree = float('inf')
                
                for node_id in remaining_nodes:
                    # Count actual remaining dependencies
                    remaining_deps = sum(1 for dep_node in graph
                                       if node_id in graph.get(dep_node, [])
                                       and dep_node in remaining_nodes)
                    if remaining_deps < min_degree:
                        min_degree = remaining_deps
                        min_node = node_id
                
                if min_node:
                    order.append(min_node)
                    remaining_nodes.remove(min_node)
                    groups.append(ExecutionGroup(level=level, nodes=[min_node]))
                    level += 1
                else:
                    # If we can't find a minimum, just add remaining nodes
                    remaining_list = list(remaining_nodes)
                    order.extend(remaining_list)
                    groups.append(ExecutionGroup(level=level, nodes=remaining_list))
                    break
        
        return order, groups
    
    def optimize_for_parallelism(
        self,
        groups: list[ExecutionGroup],
        nodes: dict[NodeID, DomainNode]
    ) -> list[ExecutionGroup]:
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