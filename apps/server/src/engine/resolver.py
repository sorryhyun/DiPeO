from typing import Dict, List, Tuple
from collections import deque, defaultdict
import logging


logger = logging.getLogger(__name__)


class DependencyResolver:
    """
    Manages dependency resolution between nodes in the execution graph.
    Determines which nodes can execute based on their dependencies and handles
    special cases like conditional branches and first-only inputs.
    """
    
    def __init__(self):
        self.logger = logger
    
    def validate_start_nodes(self, nodes_by_id: Dict[str, Dict], incoming_arrows: Dict[str, List[Dict]]) -> List[str]:
        """
        Find all start nodes in the diagram.
        A start node has type 'start' or has no incoming arrows.
        """
        start_nodes = []
        
        for node_id, node in nodes_by_id.items():
            # Get type from properties if available (ExecutionContext), otherwise from top-level
            properties = node.get("properties", {})
            node_type = properties.get("type", node["type"])
            if node_type == "start" or node_id not in incoming_arrows or not incoming_arrows[node_id]:
                start_nodes.append(node_id)
                
        return start_nodes
    
    def check_dependencies_met(
        self,
        node_id: str,
        context: 'ExecutionContext',
        allow_partial: bool = False
    ) -> Tuple[bool, List[Dict]]:
        """
        Determine if a node's dependencies are satisfied.
        
        Args:
            node_id: The node to check
            context: Current execution context
            allow_partial: Whether to allow execution with partial dependencies (for cycles)
            
        Returns:
            Tuple of (can_execute, valid_arrows)
        """
        node = context.nodes_by_id.get(node_id)
        if not node:
            self.logger.debug(f"Node {node_id} not found in context")
            return False, []
        
        # Start nodes have no dependencies
        properties = node.get("properties", {})
        node_type = properties.get("type", node["type"])
        if node_type == "start":
            self.logger.debug(f"Node {node_id} is start node - can execute")
            return True, []
        
        # Get incoming arrows
        incoming = context.incoming_arrows.get(node_id, [])
        if not incoming:
            # No dependencies means can execute
            self.logger.debug(f"Node {node_id} has no incoming arrows - can execute")
            return True, []
        
        # Check if this is a loop re-execution
        execution_count = context.node_execution_counts.get(node_id, 0)
        is_loop_reexecution = execution_count > 0
        
        self.logger.debug(f"Checking dependencies for {node_id}: {len(incoming)} incoming arrows, execution_count={execution_count}")
        
        valid_arrows = []
        required_arrows = []
        first_only_arrows = []
        
        # Categorize arrows
        for arrow in incoming:
            source_id = arrow["source"]
            source_node = context.nodes_by_id.get(source_id)
            
            if not source_node:
                self.logger.debug(f"Source node {source_id} not found for arrow to {node_id}")
                continue
                
            # Check if this is a first-only input
            is_first = self._is_first_only_arrow(arrow, node)
            self.logger.debug(f"Arrow from {source_id} to {node_id}: is_first_only={is_first}, targetHandle={arrow.get('targetHandle', '')}")
            
            if is_first:
                first_only_arrows.append(arrow)
            else:
                required_arrows.append(arrow)
        
        # Check required dependencies
        for arrow in required_arrows:
            if self._is_arrow_dependency_met(arrow, context):
                valid_arrows.append(arrow)
        
        # For first-only arrows, check if at least one is satisfied
        # and we haven't consumed first-only for this node yet
        first_only_satisfied = False
        if first_only_arrows and not context.first_only_consumed.get(node_id, False):
            for arrow in first_only_arrows:
                if self._is_arrow_dependency_met(arrow, context):
                    valid_arrows.append(arrow)
                    first_only_satisfied = True
                    break
        
        # Special case: If this is a loop re-execution (execution_count > 0),
        # and all we have are first-only arrows that were already consumed,
        # we should still allow execution if there are other valid dependencies
        if is_loop_reexecution and first_only_arrows and not required_arrows:
            # For loop iterations after the first, first-only inputs are optional
            self.logger.debug(f"Loop re-execution for {node_id}: allowing execution without first-only inputs")
            return True, valid_arrows
        
        # Check if dependencies are met
        if allow_partial and (valid_arrows or first_only_satisfied):
            # In partial mode, any satisfied dependency allows execution
            return True, valid_arrows
        
        # Normal mode: all required dependencies must be met
        all_required_met = len(valid_arrows) >= len(required_arrows)
        
        # For nodes with only first-only inputs, at least one must be satisfied
        if not required_arrows and first_only_arrows:
            return first_only_satisfied, valid_arrows
        
        return all_required_met, valid_arrows
    
    def _is_first_only_arrow(self, arrow: Dict, target_node: Dict) -> bool:
        """Check if an arrow represents a first-only input"""
        # PersonJob nodes can have first-only inputs
        properties = target_node.get("properties", {})
        node_type = properties.get("type", target_node["type"])
        if node_type in ["person_job", "person_batch_job"]:
            # Check if the arrow's targetHandle ends with "-first"
            target_handle = arrow.get("targetHandle", "")
            return target_handle.endswith("-first")
        return False
    
    def _is_arrow_dependency_met(self, arrow: Dict, context: 'ExecutionContext') -> bool:
        """Check if a specific arrow's dependency is satisfied"""
        source_id = arrow["source"]
        source_node = context.nodes_by_id.get(source_id)
        
        if not source_node:
            return False
        
        # Check if source has been executed
        if source_id not in context.node_outputs:
            return False
        
        # Special handling for condition nodes
        source_properties = source_node.get("properties", {})
        source_type = source_properties.get("type", source_node["type"])
        if source_type == "condition":
            return self._validate_condition_arrow(arrow, source_id, context)
        
        # Check if source was skipped without output
        if source_id in context.skipped_nodes:
            # Allow dependency if skipped node has output (passthrough case)
            if source_id in context.node_outputs:
                self.logger.debug(f"Skipped node {source_id} has output, allowing dependency")
                return True
            return False
        
        return True
    
    def _validate_condition_arrow(self, arrow: Dict, condition_id: str, context: 'ExecutionContext') -> bool:
        """
        Validate arrows from condition nodes based on true/false branches.
        Arrows labeled 'true' only valid if condition evaluated to true, etc.
        """
        condition_value = context.condition_values.get(condition_id)
        if condition_value is None:
            self.logger.debug(f"Condition {condition_id} has no value yet")
            return False
        
        # Check sourceHandle for true/false branch information
        source_handle = arrow.get("sourceHandle", "").lower()
        arrow_label = arrow.get("label", "").lower()
        
        self.logger.debug(f"Validating condition arrow: condition_id={condition_id}, value={condition_value}, sourceHandle={source_handle}, label={arrow_label}")
        
        # Handle true/false branch detection from sourceHandle
        if "output-true" in source_handle or "true" in source_handle:
            result = condition_value is True
        elif "output-false" in source_handle or "false" in source_handle:
            result = condition_value is False
        # Handle true/false branch labels (fallback)
        elif arrow_label in ["true", "yes", "1"]:
            result = condition_value is True
        elif arrow_label in ["false", "no", "0"]:
            result = condition_value is False
        else:
            # Unlabeled arrows from conditions are always valid
            result = True
        
        self.logger.debug(f"Condition arrow validation result: {result}")
        return result
    
    def detect_cycles(self, nodes_by_id: Dict[str, Dict], outgoing_arrows: Dict[str, List[Dict]]) -> List[List[str]]:
        """
        Use DFS to find cycles in the graph.
        Returns a list of cycles (each cycle is a list of node IDs).
        """
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node_id: str, path: List[str]) -> None:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)
            
            # Check all outgoing edges
            for arrow in outgoing_arrows.get(node_id, []):
                target_id = arrow["target"]
                
                if target_id not in visited:
                    dfs(target_id, path.copy())
                elif target_id in rec_stack:
                    # Found a cycle
                    cycle_start = path.index(target_id)
                    cycle = path[cycle_start:] + [target_id]
                    cycles.append(cycle)
            
            rec_stack.remove(node_id)
        
        # Run DFS from all unvisited nodes
        for node_id in nodes_by_id:
            if node_id not in visited:
                dfs(node_id, [])
        
        return cycles
    
    def get_next_nodes(
        self,
        node_id: str,
        context: 'ExecutionContext',
        consider_conditions: bool = True
    ) -> List[str]:
        """
        Get downstream nodes considering condition branches.
        
        Args:
            node_id: Current node ID
            context: Execution context
            consider_conditions: Whether to filter based on condition values
            
        Returns:
            List of next node IDs that should be considered for execution
        """
        next_nodes = []
        node = context.nodes_by_id.get(node_id)
        
        if not node:
            return []
        
        # Get all outgoing arrows
        outgoing = context.outgoing_arrows.get(node_id, [])
        
        for arrow in outgoing:
            target_id = arrow["target"]
            
            # Skip if target doesn't exist
            if target_id not in context.nodes_by_id:
                continue
            
            # If this is a condition node and we should consider conditions
            properties = node.get("properties", {})
            node_type = properties.get("type", node["type"])
            if consider_conditions and node_type == "condition":
                if self._validate_condition_arrow(arrow, node_id, context):
                    next_nodes.append(target_id)
            else:
                next_nodes.append(target_id)
        
        return list(set(next_nodes))  # Remove duplicates
    
    def get_dependencies(self, node_id: str, incoming_arrows: Dict[str, List[Dict]]) -> List[str]:
        """
        Get direct dependencies (upstream nodes) for a given node.
        
        Args:
            node_id: The node to get dependencies for
            incoming_arrows: Map of node IDs to incoming arrows
            
        Returns:
            List of node IDs that this node depends on
        """
        dependencies = []
        
        for arrow in incoming_arrows.get(node_id, []):
            source_id = arrow["source"]
            if source_id not in dependencies:
                dependencies.append(source_id)
        
        return dependencies
    
    def topological_sort(
        self,
        nodes_by_id: Dict[str, Dict],
        incoming_arrows: Dict[str, List[Dict]],
        outgoing_arrows: Dict[str, List[Dict]]
    ) -> List[str]:
        """
        Perform topological sort on the nodes based on dependencies.
        Returns ordered list of node IDs.
        
        Note: This will raise an exception if cycles are detected.
        """
        # Build adjacency list and in-degree count
        in_degree = defaultdict(int)
        adjacency = defaultdict(list)
        
        # Initialize all nodes
        for node_id in nodes_by_id:
            in_degree[node_id] = len(incoming_arrows.get(node_id, []))
            
            for arrow in outgoing_arrows.get(node_id, []):
                target_id = arrow["target"]
                if target_id in nodes_by_id:
                    adjacency[node_id].append(target_id)
        
        # Find all nodes with no incoming edges
        queue = deque([node_id for node_id, degree in in_degree.items() if degree == 0])
        result = []
        
        while queue:
            current = queue.popleft()
            result.append(current)
            
            # Reduce in-degree for all neighbors
            for neighbor in adjacency[current]:
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check if all nodes were processed (no cycles)
        if len(result) != len(nodes_by_id):
            # Find nodes that weren't processed (part of cycles)
            remaining = set(nodes_by_id.keys()) - set(result)
            raise ValueError(f"Cycle detected in graph. Nodes in cycle: {remaining}")
        
        return result