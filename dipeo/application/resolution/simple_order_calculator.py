"""
Simplified execution order calculation that handles cycles gracefully.
"""

from dipeo.core.execution import ExecutableEdgeV2
from dipeo.diagram_generated import DomainNode, NodeID, NodeType


class SimpleOrderCalculator:
    """Calculate execution order without treating cycles as errors."""
    
    def calculate_order(
        self,
        nodes: list[DomainNode],
        edges: list[ExecutableEdgeV2]
    ) -> tuple[list[NodeID], list, list[str]]:
        """
        Calculate a reasonable execution order.
        Cycles are expected in iterative diagrams, so we just handle them gracefully.
        Returns: (execution_order, groups, errors)
        """
        # Build dependency map
        dependencies: dict[NodeID, set[NodeID]] = {node.id: set() for node in nodes}
        for edge in edges:
            if edge.target_node_id in dependencies:
                dependencies[edge.target_node_id].add(edge.source_node_id)
        
        # Start with nodes that have no dependencies
        order: list[NodeID] = []
        remaining = {node.id for node in nodes}
        
        # First pass: add nodes with no dependencies
        while True:
            # Find nodes with no remaining dependencies
            ready = [
                node_id for node_id in remaining
                if not (dependencies[node_id] & remaining)
            ]
            
            if not ready:
                break
            
            # Add ready nodes to order
            for node_id in ready:
                order.append(node_id)
                remaining.remove(node_id)
        
        # Second pass: handle any remaining nodes (cycles)
        # Just add them in the order they appear
        if remaining:
            # For cycles, prioritize start nodes, then person jobs, then others
            node_map = {node.id: node for node in nodes}
            
            # Sort by priority
            remaining_sorted = sorted(remaining, key=lambda nid: (
                0 if node_map[nid].type == NodeType.START else
                1 if node_map[nid].type == NodeType.PERSON_JOB else
                2
            ))
            
            order.extend(remaining_sorted)
        
        # Return empty groups and no errors (cycles are not errors in our simplified approach)
        return order, [], []