from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass
from collections import deque
import logging

from .resolver import DependencyResolver

logger = logging.getLogger(__name__)


@dataclass
class ExecutionPlan:
    """Execution plan with metadata about execution order and parallelization"""
    execution_order: List[str]
    parallel_groups: List[List[str]]
    dependencies: Dict[str, List[str]]
    estimated_cost: float = 0.0
    estimated_time: float = 0.0


class ExecutionPlanner:
    """
    Creates execution plans with metadata about execution order, parallel opportunities,
    and validates execution paths.
    """
    
    def __init__(self):
        self.dependency_resolver = DependencyResolver()
        self.logger = logger
    
    def create_execution_plan(
        self,
        nodes_by_id: Dict[str, Dict],
        incoming_arrows: Dict[str, List[Dict]],
        outgoing_arrows: Dict[str, List[Dict]]
    ) -> ExecutionPlan:
        """
        Create a comprehensive execution plan for the diagram.
        
        Args:
            nodes_by_id: Map of node IDs to node objects
            incoming_arrows: Map of node IDs to incoming arrows
            outgoing_arrows: Map of node IDs to outgoing arrows
            
        Returns:
            ExecutionPlan with order, parallelization info, and estimates
        """
        # Determine execution order using topological sort
        try:
            execution_order = self.dependency_resolver.topological_sort(
                nodes_by_id, incoming_arrows, outgoing_arrows
            )
        except ValueError as e:
            # Handle cycles by using a modified approach
            self.logger.warning(f"Cycle detected, using alternative ordering: {e}")
            execution_order = self._determine_execution_order_with_cycles(
                nodes_by_id, incoming_arrows, outgoing_arrows
            )
        
        # Build dependency map
        dependencies = {}
        for node_id in nodes_by_id:
            dependencies[node_id] = self.dependency_resolver.get_dependencies(
                node_id, incoming_arrows
            )
        
        # Detect parallel execution opportunities
        parallel_groups = self.detect_parallel_execution_opportunities(
            execution_order, dependencies
        )
        
        return ExecutionPlan(
            execution_order=execution_order,
            parallel_groups=parallel_groups,
            dependencies=dependencies
        )
    
    def get_start_nodes(self, nodes_by_id: Dict[str, Dict], incoming_arrows: Dict[str, List[Dict]]) -> List[str]:
        """Get all start nodes in the diagram"""
        return self.dependency_resolver.validate_start_nodes(nodes_by_id, incoming_arrows)
    
    def get_next_nodes(
        self,
        node_id: str,
        nodes_by_id: Dict[str, Dict],
        outgoing_arrows: Dict[str, List[Dict]],
        condition_values: Optional[Dict[str, bool]] = None
    ) -> List[str]:
        """
        Get downstream nodes with conditional logic support.
        
        Args:
            node_id: Current node ID
            nodes_by_id: Map of all nodes
            outgoing_arrows: Map of outgoing arrows
            condition_values: Map of condition node outputs
            
        Returns:
            List of next node IDs to execute
        """
        next_nodes = []
        node = nodes_by_id.get(node_id)
        
        if not node:
            return []
        
        # Get all outgoing arrows
        outgoing = outgoing_arrows.get(node_id, [])
        
        for arrow in outgoing:
            target_id = arrow["target"]
            
            # Skip if target doesn't exist
            if target_id not in nodes_by_id:
                continue
            
            # Handle condition nodes
            if node["type"] == "condition" and condition_values:
                condition_value = condition_values.get(node_id)
                if condition_value is not None:
                    arrow_label = arrow.get("label", "").lower()
                    
                    # Check if arrow matches condition result
                    if arrow_label in ["true", "yes", "1"] and condition_value:
                        next_nodes.append(target_id)
                    elif arrow_label in ["false", "no", "0"] and not condition_value:
                        next_nodes.append(target_id)
                    elif arrow_label not in ["true", "yes", "1", "false", "no", "0"]:
                        # Unlabeled arrows always included
                        next_nodes.append(target_id)
            else:
                next_nodes.append(target_id)
        
        return list(set(next_nodes))  # Remove duplicates
    
    def detect_parallel_execution_opportunities(
        self,
        execution_order: List[str],
        dependencies: Dict[str, List[str]]
    ) -> List[List[str]]:
        """
        Identify nodes that can run in parallel.
        Uses level-based approach: nodes with satisfied dependencies form parallel groups.
        
        Args:
            execution_order: Topologically sorted node order
            dependencies: Map of node ID to dependency node IDs
            
        Returns:
            List of parallel groups (each group can execute simultaneously)
        """
        if not execution_order:
            return []
        
        # Track which nodes have been assigned to a level
        assigned = set()
        parallel_groups = []
        
        # Create levels based on dependencies
        remaining_nodes = set(execution_order)
        
        while remaining_nodes:
            # Find all nodes whose dependencies are satisfied
            current_level = []
            
            for node_id in remaining_nodes:
                node_deps = set(dependencies.get(node_id, []))
                
                # Check if all dependencies are assigned
                if node_deps.issubset(assigned):
                    current_level.append(node_id)
            
            if not current_level:
                # This shouldn't happen with a valid topological sort
                # But handle it gracefully by taking the first remaining node
                current_level = [next(iter(remaining_nodes))]
            
            # Add current level to parallel groups
            parallel_groups.append(current_level)
            
            # Mark these nodes as assigned
            for node_id in current_level:
                assigned.add(node_id)
                remaining_nodes.remove(node_id)
        
        return parallel_groups
    
    def validate_execution_path(
        self,
        execution_sequence: List[str],
        dependencies: Dict[str, List[str]]
    ) -> bool:
        """
        Validate if a given execution sequence is valid.
        Checks that all dependencies are satisfied before each node executes.
        
        Args:
            execution_sequence: Proposed execution order
            dependencies: Map of node dependencies
            
        Returns:
            True if the sequence is valid, False otherwise
        """
        executed = set()
        
        for node_id in execution_sequence:
            # Check if all dependencies have been executed
            node_deps = dependencies.get(node_id, [])
            
            for dep in node_deps:
                if dep not in executed:
                    self.logger.error(
                        f"Invalid execution sequence: {node_id} depends on {dep} "
                        f"which hasn't been executed yet"
                    )
                    return False
            
            executed.add(node_id)
        
        return True
    
    def _determine_execution_order_with_cycles(
        self,
        nodes_by_id: Dict[str, Dict],
        incoming_arrows: Dict[str, List[Dict]],
        outgoing_arrows: Dict[str, List[Dict]]
    ) -> List[str]:
        """
        Determine execution order when cycles are present.
        Uses a modified BFS approach that breaks cycles at loop control points.
        """
        # Start with nodes that have no dependencies
        start_nodes = self.get_start_nodes(nodes_by_id, incoming_arrows)
        if not start_nodes:
            # If no clear start nodes, pick one arbitrarily
            start_nodes = [next(iter(nodes_by_id.keys()))]
        
        visited = set()
        execution_order = []
        queue = deque(start_nodes)
        
        # Track nodes we've seen but not yet processed (for cycle detection)
        seen = set(start_nodes)
        
        while queue:
            current = queue.popleft()
            
            # Skip if already processed
            if current in visited:
                continue
            
            # Check if dependencies are met (excluding cycles)
            deps = self.dependency_resolver.get_dependencies(current, incoming_arrows)
            unmet_deps = [d for d in deps if d not in visited and d != current]
            
            # If there are unmet dependencies that we haven't seen yet, defer this node
            new_deps = [d for d in unmet_deps if d not in seen]
            if new_deps:
                # Add the dependencies to the queue first
                for dep in new_deps:
                    if dep not in seen:
                        queue.append(dep)
                        seen.add(dep)
                # Re-add current node to process later
                queue.append(current)
                continue
            
            # Process the node
            visited.add(current)
            execution_order.append(current)
            
            # Add downstream nodes to queue
            next_nodes = []
            for arrow in outgoing_arrows.get(current, []):
                target = arrow["target"]
                if target not in seen and target in nodes_by_id:
                    next_nodes.append(target)
                    seen.add(target)
            
            queue.extend(next_nodes)
        
        # Add any remaining nodes (disconnected components)
        for node_id in nodes_by_id:
            if node_id not in visited:
                execution_order.append(node_id)
        
        return execution_order
    
