"""Execution Domain Service - Core business logic for diagram execution."""

from typing import Any

from ..value_objects import (
    ExecutionFlow,
    ExecutionMode,
    ExecutionPlan,
    ExecutionStep,
    FlowIssue,
    FlowIssueType,
    FlowValidationResult,
)


class ExecutionDomainService:
    """Domain service for execution-related business logic."""
    
    def validate_execution_flow(self, diagram: Any) -> FlowValidationResult:
        """
        Validate that a diagram has a valid execution flow.
        
        Args:
            diagram: Diagram object with nodes and edges
            
        Returns:
            FlowValidationResult with validation status and issues
        """
        result = FlowValidationResult(is_valid=True, issues=[])
        
        # Extract flow structure
        nodes = {node.id: node.type for node in diagram.nodes}
        connections = {}
        for arrow in diagram.arrows:
            if arrow.source not in connections:
                connections[arrow.source] = set()
            connections[arrow.source].add(arrow.target)
        
        # Find start and endpoint nodes
        start_nodes = {
            node_id for node_id, node_type in nodes.items()
            if node_type == "start"
        }
        endpoint_nodes = {
            node_id for node_id, node_type in nodes.items()
            if node_type == "endpoint"
        }
        
        flow = ExecutionFlow(
            nodes=nodes,
            connections=connections,
            start_nodes=start_nodes,
            endpoint_nodes=endpoint_nodes
        )
        
        # Check for start node
        if not start_nodes:
            issue = FlowIssue(
                issue_type=FlowIssueType.NO_START_NODE,
                message="Diagram must have at least one start node"
            )
            result = result.add_issue(issue)
        
        # Check for endpoint node
        if not endpoint_nodes:
            issue = FlowIssue(
                issue_type=FlowIssueType.NO_ENDPOINT_NODE,
                message="Diagram should have at least one endpoint node"
            )
            result = result.add_issue(issue)
        
        # Check for circular dependencies
        cycles = flow.find_cycles()
        for cycle in cycles:
            issue = FlowIssue(
                issue_type=FlowIssueType.CIRCULAR_DEPENDENCY,
                message=f"Circular dependency detected: {' -> '.join(cycle)}",
                related_nodes=set(cycle)
            )
            result = result.add_issue(issue)
        
        # Check for unreachable nodes
        unreachable = flow.find_unreachable_nodes()
        for node_id in unreachable:
            issue = FlowIssue(
                issue_type=FlowIssueType.UNREACHABLE_NODE,
                node_id=node_id,
                message=f"Node {node_id} is not reachable from any start node"
            )
            result = result.add_issue(issue)
        
        # Validate node connections based on node types
        for node in diagram.nodes:
            node_id = node.id
            node_type = node.type
            
            # Start nodes should not have incoming connections
            if node_type == "start":
                incoming = flow.get_dependencies(node_id)
                if incoming:
                    issue = FlowIssue(
                        issue_type=FlowIssueType.INVALID_CONNECTION,
                        node_id=node_id,
                        message="Start node cannot have incoming connections",
                        related_nodes=incoming
                    )
                    result = result.add_issue(issue)
            
            # Endpoint nodes should not have outgoing connections
            elif node_type == "endpoint":
                outgoing = connections.get(node_id, set())
                if outgoing:
                    issue = FlowIssue(
                        issue_type=FlowIssueType.INVALID_CONNECTION,
                        node_id=node_id,
                        message="Endpoint node cannot have outgoing connections",
                        related_nodes=outgoing
                    )
                    result = result.add_issue(issue)
            
            # Condition nodes should have at least 2 outgoing connections
            # Note: In DiPeO, arrows connect to handles (e.g., node_3_true_output)
            # so we can't reliably validate condition node connections here
            # This validation would need handle-aware connection mapping
        
        return result
    
    def calculate_execution_order(self, nodes: list[Any]) -> list[str]:
        """
        Calculate the execution order for nodes using topological sort.
        
        Args:
            nodes: List of node objects with id and connections
            
        Returns:
            List of node IDs in execution order
        """
        # Build adjacency list and in-degree count
        graph = {}
        in_degree = {}
        
        for node in nodes:
            node_id = node.id
            graph[node_id] = []
            if node_id not in in_degree:
                in_degree[node_id] = 0
        
        # Process edges
        for node in nodes:
            if hasattr(node, 'connections'):
                for target in node.connections:
                    graph[node.id].append(target)
                    in_degree[target] = in_degree.get(target, 0) + 1
        
        # Kahn's algorithm for topological sort
        queue = [node_id for node_id, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            current = queue.pop(0)
            result.append(current)
            
            for neighbor in graph.get(current, []):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)
        
        # Check if all nodes were processed (no cycles)
        if len(result) != len(nodes):
            # Return partial order, cycle detection should be done separately
            remaining = [n.id for n in nodes if n.id not in result]
            result.extend(remaining)
        
        return result
    
    def determine_parallelization(self, nodes: list[Any], arrows: list[Any] = None) -> ExecutionPlan:
        """
        Determine which nodes can be executed in parallel.
        
        Args:
            nodes: List of node objects
            arrows: List of arrow/edge objects (optional)
            
        Returns:
            ExecutionPlan with parallel execution groups
        """
        # Build dependency graph
        dependencies = {}
        node_types = {}
        
        for node in nodes:
            node_id = node.id if hasattr(node, 'id') else node.get('id')
            node_type = node.type if hasattr(node, 'type') else node.get('node_type', node.get('type'))
            node_types[node_id] = node_type
            dependencies[node_id] = set()
        
        # Find dependencies based on arrows if provided
        if arrows:
            for arrow in arrows:
                source = arrow.source if hasattr(arrow, 'source') else arrow.get('source')
                target = arrow.target if hasattr(arrow, 'target') else arrow.get('target')
                if target in dependencies:
                    dependencies[target].add(source)
        
        # Create execution steps
        steps = []
        for node in nodes:
            node_id = node.id if hasattr(node, 'id') else node.get('id')
            node_type = node.type if hasattr(node, 'type') else node.get('node_type', node.get('type'))
            
            # Determine execution mode
            if node_type == "condition":
                mode = ExecutionMode.CONDITIONAL
            elif node_type in ["person_batch", "api_batch"]:
                mode = ExecutionMode.PARALLEL
            else:
                mode = ExecutionMode.SEQUENTIAL
            
            # Get condition safely
            condition = None
            if node_type == "condition":
                if hasattr(node, 'condition'):
                    condition = node.condition
                elif hasattr(node, 'get'):
                    condition = node.get('condition')
            
            step = ExecutionStep(
                node_id=node_id,
                dependencies=dependencies[node_id],
                execution_mode=mode,
                condition=condition
            )
            steps.append(step)
        
        # Identify parallel groups using level-based approach
        levels = self._calculate_levels(dependencies)
        parallel_groups = {}
        
        for level, node_ids in levels.items():
            # Nodes at the same level with no dependencies on each other can run in parallel
            for i, node_id in enumerate(node_ids):
                # Check if this node can be parallelized
                node_type = node_types[node_id]
                if node_type not in ["condition", "start", "endpoint"]:
                    # Find other nodes at same level that don't depend on this one
                    parallel_with = set()
                    for other_id in node_ids:
                        if other_id != node_id:
                            # Check if they have dependencies on each other
                            if (node_id not in dependencies[other_id] and 
                                other_id not in dependencies[node_id]):
                                parallel_with.add(other_id)
                    
                    if parallel_with:
                        # Create or update parallel group
                        group_id = level
                        if group_id not in parallel_groups:
                            parallel_groups[group_id] = set()
                        parallel_groups[group_id].add(node_id)
                        parallel_groups[group_id].update(parallel_with)
        
        # Find entry points (nodes with no dependencies)
        entry_points = {
            node_id for node_id, deps in dependencies.items()
            if not deps
        }
        
        return ExecutionPlan(
            steps=steps,
            entry_points=entry_points,
            parallel_groups=parallel_groups
        )
    
    def _calculate_levels(self, dependencies: dict[str, set[str]]) -> dict[int, list[str]]:
        """Calculate execution levels for nodes."""
        levels = {}
        node_level = {}
        
        # Calculate level for each node
        def calculate_node_level(node_id: str) -> int:
            if node_id in node_level:
                return node_level[node_id]
            
            deps = dependencies.get(node_id, set())
            if not deps:
                level = 0
            else:
                level = max(calculate_node_level(dep) for dep in deps) + 1
            
            node_level[node_id] = level
            return level
        
        # Calculate levels for all nodes
        for node_id in dependencies:
            level = calculate_node_level(node_id)
            if level not in levels:
                levels[level] = []
            levels[level].append(node_id)
        
        return levels
    
    def validate_node_inputs(
        self,
        node_type: str,
        inputs: dict[str, Any],
        required_inputs: dict[str, str]
    ) -> tuple[bool, str | None]:
        """
        Validate that a node has all required inputs with correct types.
        
        Args:
            node_type: Type of the node
            inputs: Provided inputs
            required_inputs: Map of input name to expected type
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check for missing required inputs
        for input_name, expected_type in required_inputs.items():
            if input_name not in inputs:
                return False, f"Missing required input '{input_name}' for {node_type} node"
            
            # Basic type validation
            value = inputs[input_name]
            if expected_type == "string" and not isinstance(value, str):
                return False, f"Input '{input_name}' must be a string"
            elif expected_type == "number" and not isinstance(value, (int, float)):
                return False, f"Input '{input_name}' must be a number"
            elif expected_type == "boolean" and not isinstance(value, bool):
                return False, f"Input '{input_name}' must be a boolean"
            elif expected_type == "array" and not isinstance(value, list):
                return False, f"Input '{input_name}' must be an array"
            elif expected_type == "object" and not isinstance(value, dict):
                return False, f"Input '{input_name}' must be an object"
        
        return True, None
    
    def calculate_execution_timeout(
        self,
        node_type: str,
        node_config: dict[str, Any]
    ) -> int:
        """
        Calculate appropriate timeout for node execution.
        
        Args:
            node_type: Type of the node
            node_config: Node configuration
            
        Returns:
            Timeout in seconds
        """
        # Default timeouts by node type
        default_timeouts = {
            "person": 60,  # LLM calls can take time
            "person_batch": 300,  # Batch operations need more time
            "api": 30,
            "api_batch": 120,
            "code": 30,
            "db": 10,
            "condition": 5,
            "start": 1,
            "endpoint": 1,
        }
        
        # Get base timeout
        base_timeout = default_timeouts.get(node_type, 30)
        
        # Adjust based on configuration
        if "timeout" in node_config:
            return int(node_config["timeout"])
        
        # Adjust for batch size if applicable
        if node_type.endswith("_batch") and "batch_size" in node_config:
            batch_size = node_config["batch_size"]
            # Scale timeout with batch size
            base_timeout = base_timeout + (batch_size * 2)
        
        return base_timeout