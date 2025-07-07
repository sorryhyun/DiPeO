"""Domain service for execution flow logic."""

from typing import List, Dict, Any, Optional, Set
import logging

from dipeo.models import DomainDiagram, NodeType, DomainNode

log = logging.getLogger(__name__)


class ExecutionFlowService:
    """Service for managing execution flow business logic."""
    
    def is_node_dependencies_satisfied(
        self,
        node: DomainNode,
        diagram: DomainDiagram,
        executed_nodes: Set[str],
        node_outputs: Dict[str, Any],
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> bool:
        """Determine if a node's dependencies are satisfied.
        
        Business rules:
        - Start nodes have no dependencies
        - Person job nodes with "first" handle only need inputs on first execution
        - All other nodes need all their dependencies executed
        """
        # Start nodes have no dependencies
        if node.type == NodeType.db:
            # Check if it's a start node (no incoming edges)
            incoming_edges = [
                edge for edge in diagram.edges 
                if edge.target == node.id
            ]
            if not incoming_edges:
                return True
        
        # Get all nodes that this node depends on
        dependency_nodes = self._get_dependency_nodes(node, diagram)
        
        # Special handling for person_job nodes with "first" handle
        if node.type == NodeType.person_job:
            exec_count = node_exec_counts.get(node.id, 0) if node_exec_counts else 0
            
            # Check if this is not the first execution
            if exec_count > 0:
                # For subsequent executions, only check non-"first" dependencies
                non_first_dependencies = []
                for dep_id in dependency_nodes:
                    # Find edges from dependency to this node
                    from dipeo.models import parse_handle_id
                    connecting_edges = []
                    for edge in diagram.arrows:
                        source_node_id, _ = parse_handle_id(edge.source)
                        target_node_id, target_handle = parse_handle_id(edge.target)
                        if source_node_id == dep_id and target_node_id == node.id:
                            connecting_edges.append((edge, target_handle))
                    
                    # Check if any edge has targetHandle != "first"
                    has_non_first = any(
                        target_handle != "first" 
                        for edge, target_handle in connecting_edges
                    )
                    if has_non_first:
                        non_first_dependencies.append(dep_id)
                
                dependency_nodes = non_first_dependencies
        
        # Check if all dependencies have been executed
        for dep_id in dependency_nodes:
            if dep_id not in executed_nodes:
                return False
        
        return True
    
    def should_execution_continue(
        self,
        ready_nodes: List[DomainNode],
        executed_nodes: Set[str],
        diagram: DomainDiagram,
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> bool:
        """Determine if execution should continue.
        
        Business rules:
        - Stop if all endpoints have been executed
        - Stop if only unexecutable nodes remain
        - Stop if nodes have reached max iterations
        """
        # Check if all endpoints have been executed
        endpoint_nodes = [
            node for node in diagram.nodes 
            if node.type == NodeType.endpoint
        ]
        
        if endpoint_nodes:
            all_endpoints_executed = all(
                endpoint.id in executed_nodes 
                for endpoint in endpoint_nodes
            )
            if all_endpoints_executed:
                log.debug("All endpoints executed, stopping")
                return False
        
        # Check if we have any nodes that can still execute
        if not ready_nodes:
            log.debug("No ready nodes, stopping")
            return False
        
        # Check if nodes have reached their max iterations
        can_execute = False
        for node in ready_nodes:
            if self.can_node_execute(node, node_exec_counts):
                can_execute = True
                break
        
        if not can_execute:
            log.debug("No nodes can execute (max iterations reached), stopping")
            return False
        
        return True
    
    def get_ready_nodes(
        self,
        diagram: DomainDiagram,
        executed_nodes: Set[str],
        node_outputs: Dict[str, Any],
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> List[DomainNode]:
        """Get all nodes that are ready to execute.
        
        A node is ready if:
        - It hasn't exceeded its max iterations
        - All its dependencies are satisfied
        """
        ready_nodes = []
        
        for node in diagram.nodes:
            # Skip if node can't execute anymore
            if not self.can_node_execute(node, node_exec_counts):
                continue
            
            # Check dependencies
            if self.is_node_dependencies_satisfied(
                node, diagram, executed_nodes, node_outputs, node_exec_counts
            ):
                ready_nodes.append(node)
        
        return ready_nodes
    
    def can_node_execute(
        self,
        node: DomainNode,
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> bool:
        """Check if a node can execute based on its max iterations.
        
        Business rules:
        - Nodes without max_iteration can always execute
        - Nodes with max_iteration stop after reaching the limit
        """
        if not node_exec_counts:
            return True
        
        exec_count = node_exec_counts.get(node.id, 0)
        
        # Check max iterations for person_job nodes
        if node.type == NodeType.person_job and node.data:
            max_iter = node.data.get("max_iteration", 1)
            if exec_count >= max_iter:
                return False
        
        # Check max iterations for person_batch_job nodes
        if node.type == NodeType.person_batch_job and node.data:
            max_iter = node.data.get("max_iteration", 1)
            if exec_count >= max_iter:
                return False
        
        return True
    
    def _get_dependency_nodes(
        self,
        node: DomainNode,
        diagram: DomainDiagram,
    ) -> List[str]:
        """Get all nodes that this node depends on."""
        dependency_ids = []
        
        # Find all edges pointing to this node
        from dipeo.models import parse_handle_id
        for edge in diagram.arrows:
            target_node_id, _ = parse_handle_id(edge.target)
            if target_node_id == node.id:
                source_node_id, _ = parse_handle_id(edge.source)
                dependency_ids.append(source_node_id)
        
        return dependency_ids