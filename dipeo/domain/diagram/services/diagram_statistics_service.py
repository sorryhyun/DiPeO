"""Domain service for diagram statistics and analysis."""

from typing import Any

from dipeo.models import DomainDiagram, NodeType


class DiagramStatisticsService:
    """Service for calculating diagram statistics and analysis."""

    def calculate_statistics(self, diagram: DomainDiagram) -> dict[str, Any]:
        """Calculate comprehensive statistics for a diagram."""
        node_count = len(diagram.nodes) if diagram.nodes else 0
        arrow_count = len(diagram.arrows) if diagram.arrows else 0
        person_count = len(diagram.persons) if diagram.persons else 0
        
        # Count node types
        node_types = {}
        if diagram.nodes:
            nodes_list = list(diagram.nodes.values()) if isinstance(diagram.nodes, dict) else diagram.nodes
            for node in nodes_list:
                node_type = getattr(node, "type", "unknown")
                if isinstance(node_type, NodeType):
                    node_type_str = node_type.value
                else:
                    node_type_str = str(node_type)
                node_types[node_type_str] = node_types.get(node_type_str, 0) + 1
        
        return {
            "total_nodes": node_count,
            "total_arrows": arrow_count,
            "total_persons": person_count,
            "node_types": node_types,
            "complexity_score": node_count + arrow_count,
            "has_cycles": self._detect_cycles(diagram),
            "is_connected": self._check_connectivity(diagram),
            "has_start_node": self._has_start_node(diagram),
            "has_end_node": self._has_end_node(diagram),
        }

    def _detect_cycles(self, diagram: DomainDiagram) -> bool:
        """Detect if the diagram has cycles using DFS."""
        if not diagram.arrows:
            return False
        
        # Build adjacency list
        graph = {}
        arrows_list = list(diagram.arrows.values()) if isinstance(diagram.arrows, dict) else diagram.arrows
        
        for arrow in arrows_list:
            source = getattr(arrow, "source", None)
            target = getattr(arrow, "target", None)
            if source and target:
                if source not in graph:
                    graph[source] = []
                graph[source].append(target)
        
        # DFS cycle detection
        visited = set()
        rec_stack = set()
        
        def has_cycle(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in graph.get(node, []):
                if neighbor not in visited:
                    if has_cycle(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True
            
            rec_stack.remove(node)
            return False
        
        for node in graph:
            if node not in visited:
                if has_cycle(node):
                    return True
        
        return False

    def _check_connectivity(self, diagram: DomainDiagram) -> bool:
        """Check if the diagram is fully connected."""
        if not diagram.nodes or len(diagram.nodes) <= 1:
            return True
        
        # Build undirected adjacency list
        graph = {}
        nodes_list = list(diagram.nodes.values()) if isinstance(diagram.nodes, dict) else diagram.nodes
        node_ids = {getattr(node, "id", str(i)) for i, node in enumerate(nodes_list)}
        
        for node_id in node_ids:
            graph[node_id] = set()
        
        if diagram.arrows:
            arrows_list = list(diagram.arrows.values()) if isinstance(diagram.arrows, dict) else diagram.arrows
            for arrow in arrows_list:
                source = getattr(arrow, "source", None)
                target = getattr(arrow, "target", None)
                if source and target and source in node_ids and target in node_ids:
                    graph[source].add(target)
                    graph[target].add(source)
        
        # BFS to check connectivity
        if not node_ids:
            return True
        
        visited = set()
        queue = [next(iter(node_ids))]
        
        while queue:
            node = queue.pop(0)
            if node not in visited:
                visited.add(node)
                queue.extend(graph.get(node, set()) - visited)
        
        return len(visited) == len(node_ids)

    def _has_start_node(self, diagram: DomainDiagram) -> bool:
        """Check if diagram has at least one START node."""
        if not diagram.nodes:
            return False
        
        nodes_list = list(diagram.nodes.values()) if isinstance(diagram.nodes, dict) else diagram.nodes
        for node in nodes_list:
            node_type = getattr(node, "type", None)
            if node_type == NodeType.START or node_type == "START":
                return True
        
        return False

    def _has_end_node(self, diagram: DomainDiagram) -> bool:
        """Check if diagram has at least one END node."""
        if not diagram.nodes:
            return False
        
        nodes_list = list(diagram.nodes.values()) if isinstance(diagram.nodes, dict) else diagram.nodes
        for node in nodes_list:
            node_type = getattr(node, "type", None)
            if node_type == NodeType.END or node_type == "END":
                return True
        
        return False

    def generate_safe_filename(self, diagram_name: str, extension: str = ".json") -> str:
        """Generate a safe filename from diagram name."""
        safe_name = "".join(
            c for c in diagram_name if c.isalnum() or c in " -_"
        )
        safe_name = safe_name[:50]  # Limit length
        if not safe_name.endswith(extension):
            safe_name += extension
        return safe_name