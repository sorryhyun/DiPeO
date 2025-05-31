"""Execution planner integrating logic from dynamic_executor.py."""

from typing import List, Dict, Set, Optional, Any
from collections import defaultdict, deque
import logging

from ..core.execution_context import ExecutionContext
from .dependency_resolver import DependencyResolver
from apps.server.src.constants import NodeType
from apps.server.src.utils.arrow_utils import ArrowUtils

logger = logging.getLogger(__name__)


class ExecutionPlanner:
    """Plans execution order and handles execution planning logic."""
    
    def __init__(self, context: ExecutionContext, dependency_resolver: DependencyResolver):
        self.context = context
        self.dependency_resolver = dependency_resolver
    
    def create_execution_plan(self) -> Dict[str, Any]:
        """Create execution plan with validation and metadata (from dynamic_executor)."""
        start_nodes = self.dependency_resolver.validate_start_nodes()
        cycles = self.dependency_resolver.detect_cycles()

        return {
            "start_nodes": start_nodes,
            "has_cycles": len(cycles) > 0,
            "cycle_nodes": cycles,
            "total_nodes": len(self.context.nodes_by_id),
            "total_arrows": len(self._get_all_arrows()),
            "node_types": {node_id: node.get("type", "unknown") for node_id, node in self.context.nodes_by_id.items()}
        }
    
    def get_start_nodes(self) -> List[str]:
        """Get all start nodes in the diagram."""
        return [
            node_id
            for node_id, node in self.context.nodes_by_id.items()
            if node.get('type') == 'startNode'
        ]
    
    def get_next_nodes(self, node_id: str, output: Any = None) -> List[str]:
        """Get the next nodes to execute based on current node output."""
        next_nodes = []
        outgoing = self.context.outgoing_arrows.get(node_id, [])
        
        for arrow in outgoing:
            target_id = ArrowUtils.get_target(arrow)
            if not target_id:
                continue
                
            # Handle conditional arrows
            if self._is_conditional_arrow(arrow) and isinstance(output, bool):
                arrow_label = self._get_arrow_label(arrow)
                if (arrow_label == 'true' and output) or (arrow_label == 'false' and not output):
                    next_nodes.append(target_id)
            else:
                # Non-conditional arrow
                next_nodes.append(target_id)
        
        return next_nodes
    
    def _is_conditional_arrow(self, arrow: dict) -> bool:
        """Check if arrow is conditional based on label."""
        label = self._get_arrow_label(arrow)
        return label in ['true', 'false']
    
    def _get_arrow_label(self, arrow: dict) -> str:
        """Get arrow label for conditional logic."""
        # Check multiple possible locations for the label
        label = arrow.get('label', '')
        if not label:
            # Check sourceHandle for condition output patterns
            source_handle = arrow.get('sourceHandle', '')
            if source_handle.endswith('-output-true'):
                label = 'true'
            elif source_handle.endswith('-output-false'):
                label = 'false'
            else:
                # Check arrow data
                label = arrow.get('data', {}).get('label', '')
        
        return label.lower() if label else ''
    
    def _get_all_arrows(self) -> List[dict]:
        """Get all arrows from the context."""
        all_arrows = []
        for arrows in self.context.outgoing_arrows.values():
            all_arrows.extend(arrows)
        return all_arrows
    
    def detect_parallel_execution_opportunities(self) -> List[Set[str]]:
        """Identify nodes that can be executed in parallel."""
        parallel_groups = []
        processed = set()
        
        while len(processed) < len(self.context.nodes_by_id):
            # Find nodes with no unprocessed dependencies
            ready_nodes = set()
            
            for node_id in self.context.nodes_by_id:
                if node_id in processed:
                    continue
                
                # Check if all dependencies are processed
                deps = set(self.dependency_resolver.get_dependencies(node_id))
                if deps.issubset(processed):
                    ready_nodes.add(node_id)
            
            if not ready_nodes:
                # Handle cycles or disconnected nodes
                remaining = set(self.context.nodes_by_id.keys()) - processed
                if remaining:
                    ready_nodes.add(next(iter(remaining)))
            
            if ready_nodes:
                parallel_groups.append(ready_nodes)
                processed.update(ready_nodes)
        
        return parallel_groups
    
    def validate_execution_path(self, path: List[str]) -> Dict[str, Any]:
        """Validate if an execution path is valid."""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        executed = set()
        
        for i, node_id in enumerate(path):
            if node_id not in self.context.nodes_by_id:
                validation_result["is_valid"] = False
                validation_result["errors"].append(f"Node {node_id} not found in diagram")
                continue
            
            # Check dependencies
            deps = set(self.dependency_resolver.get_dependencies(node_id))
            missing_deps = deps - executed
            
            if missing_deps:
                validation_result["is_valid"] = False
                validation_result["errors"].append(
                    f"Node {node_id} at position {i} has unmet dependencies: {missing_deps}"
                )
            
            executed.add(node_id)
        
        return validation_result