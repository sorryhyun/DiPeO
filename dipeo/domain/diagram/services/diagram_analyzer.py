# Graph analysis functions for diagrams

from collections import defaultdict, deque

from dipeo.models import DomainDiagram, NodeType, extract_node_id_from_handle


class DiagramAnalyzer:
    # Pure functions for diagram analysis
    
    @staticmethod
    def find_cycles(diagram: DomainDiagram) -> list[list[str]]:
        # Find all cycles in the diagram
        # Build adjacency list
        graph = defaultdict(list)
        for arrow in diagram.arrows:
            source_id = extract_node_id_from_handle(arrow.source)
            target_id = extract_node_id_from_handle(arrow.target)
            graph[source_id].append(target_id)
        
        # Track visited nodes and recursion stack
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node: str, path: list[str]) -> None:
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in graph[node]:
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
            
            rec_stack.remove(node)
        
        # Check all nodes
        for node in diagram.nodes:
            if node.id not in visited:
                dfs(node.id, [])
        
        return cycles
    
    @staticmethod
    def find_critical_path(diagram: DomainDiagram) -> list[str]:
        # Find the longest path from start to endpoint
        # Build adjacency list
        graph = defaultdict(list)
        for arrow in diagram.arrows:
            source_id = extract_node_id_from_handle(arrow.source)
            target_id = extract_node_id_from_handle(arrow.target)
            graph[source_id].append(target_id)
        
        # Find all paths from start nodes to endpoints
        start_nodes = [n.id for n in diagram.nodes if n.type == NodeType.start]
        endpoint_nodes = set(n.id for n in diagram.nodes if n.type == NodeType.endpoint)
        
        longest_path = []
        
        def dfs_paths(node: str, path: list[str], visited: set[str]):
            if node in endpoint_nodes:
                if len(path) > len(longest_path):
                    longest_path.clear()
                    longest_path.extend(path)
                return
            
            for neighbor in graph[node]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    dfs_paths(neighbor, path + [neighbor], visited.copy())
        
        for start in start_nodes:
            dfs_paths(start, [start], {start})
        
        return longest_path
    
    @staticmethod
    def calculate_node_depths(diagram: DomainDiagram) -> dict[str, int]:
        # Calculate the depth of each node from start nodes
        # Build adjacency list
        graph = defaultdict(list)
        in_degree = defaultdict(int)
        
        for arrow in diagram.arrows:
            source_id = extract_node_id_from_handle(arrow.source)
            target_id = extract_node_id_from_handle(arrow.target)
            graph[source_id].append(target_id)
            in_degree[target_id] += 1
        
        # Initialize depths
        depths = {}
        queue = deque()
        
        # Start with nodes that have no incoming edges or are start nodes
        for node in diagram.nodes:
            if node.type == NodeType.start or in_degree[node.id] == 0:
                depths[node.id] = 0
                queue.append(node.id)
        
        # BFS to calculate depths
        while queue:
            current = queue.popleft()
            current_depth = depths[current]
            
            for neighbor in graph[current]:
                # Update depth if we found a longer path
                if neighbor not in depths or depths[neighbor] < current_depth + 1:
                    depths[neighbor] = current_depth + 1
                
                # Decrease in-degree
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0 and neighbor not in depths:
                    queue.append(neighbor)
        
        return depths
    
    @staticmethod
    def find_bottlenecks(diagram: DomainDiagram) -> list[str]:
        # Find nodes that all paths must go through
        # Find nodes that lie on all paths from start to endpoint
        start_nodes = [n.id for n in diagram.nodes if n.type == NodeType.start]
        endpoint_nodes = [n.id for n in diagram.nodes if n.type == NodeType.endpoint]
        
        if not start_nodes or not endpoint_nodes:
            return []
        
        # Build graph
        graph = defaultdict(list)
        for arrow in diagram.arrows:
            source_id = extract_node_id_from_handle(arrow.source)
            target_id = extract_node_id_from_handle(arrow.target)
            graph[source_id].append(target_id)
        
        # Find all paths
        all_paths = []
        
        def find_paths(current: str, target: str, path: list[str], visited: set[str]):
            if current == target:
                all_paths.append(path.copy())
                return
            
            for neighbor in graph[current]:
                if neighbor not in visited:
                    visited.add(neighbor)
                    find_paths(neighbor, target, path + [neighbor], visited.copy())
        
        # Find all paths from any start to any endpoint
        for start in start_nodes:
            for endpoint in endpoint_nodes:
                find_paths(start, endpoint, [start], {start})
        
        if not all_paths:
            return []
        
        # Find common nodes in all paths (excluding start and endpoints)
        common_nodes = set(all_paths[0]) - set(start_nodes) - set(endpoint_nodes)
        for path in all_paths[1:]:
            common_nodes &= set(path)
        
        return list(common_nodes)
    
    @staticmethod
    def calculate_node_fanout(diagram: DomainDiagram) -> dict[str, int]:
        # Calculate the fanout (number of outgoing connections) for each node
        fanout = defaultdict(int)
        
        for arrow in diagram.arrows:
            source_id = extract_node_id_from_handle(arrow.source)
            fanout[source_id] += 1
        
        # Include nodes with no outgoing connections
        for node in diagram.nodes:
            if node.id not in fanout:
                fanout[node.id] = 0
        
        return dict(fanout)
    
    @staticmethod
    def find_parallel_paths(diagram: DomainDiagram) -> list[tuple[str, str, list[list[str]]]]:
        # Find nodes that have multiple paths between them
        graph = defaultdict(list)
        for arrow in diagram.arrows:
            source_id = extract_node_id_from_handle(arrow.source)
            target_id = extract_node_id_from_handle(arrow.target)
            graph[source_id].append(target_id)
        
        parallel_paths = []
        
        # Check each pair of nodes
        node_ids = [n.id for n in diagram.nodes]
        for i, source in enumerate(node_ids):
            for target in node_ids[i+1:]:
                paths = []
                
                def find_paths(current: str, dest: str, path: list[str], visited: set[str]):
                    if current == dest:
                        paths.append(path.copy())
                        return
                    
                    for neighbor in graph[current]:
                        if neighbor not in visited:
                            visited.add(neighbor)
                            find_paths(neighbor, dest, path + [neighbor], visited.copy())
                
                find_paths(source, target, [source], {source})
                
                if len(paths) > 1:
                    parallel_paths.append((source, target, paths))
        
        return parallel_paths