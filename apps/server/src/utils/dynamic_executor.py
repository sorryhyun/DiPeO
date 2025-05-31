import logging
from typing import Dict, List, Set, Tuple, Optional, Any
from collections import deque
from dataclasses import dataclass
from .arrow_utils import ArrowUtils
from ..constants import NodeType

logger = logging.getLogger(__name__)


@dataclass
class ArrowValidation:
    """Results from validating an arrow dependency."""
    is_valid: bool
    arrow: dict
    reason: Optional[str] = None


class DynamicExecutor:
    """Handles dynamic execution order based on condition evaluations."""

    def __init__(self, nodes: List[dict], arrows: List[dict]):
        self.nodes = nodes
        self.arrows = arrows
        self.nodes_by_id = {n["id"]: n for n in nodes}

        self.outgoing_arrows: Dict[str, List[dict]] = {}
        self.incoming_arrows: Dict[str, List[dict]] = {}

        for arrow in arrows:
            src = ArrowUtils.get_source(arrow)
            tgt = ArrowUtils.get_target(arrow)

            if src:
                if src not in self.outgoing_arrows:
                    self.outgoing_arrows[src] = []
                self.outgoing_arrows[src].append(arrow)

            if tgt:
                if tgt not in self.incoming_arrows:
                    self.incoming_arrows[tgt] = []
                self.incoming_arrows[tgt].append(arrow)
        
        self.first_only_consumed: Dict[str, bool] = {}

    def validate_start_nodes(self) -> List[str]:
        """Validate and return start node IDs."""
        start_nodes = []
        for nid, node in self.nodes_by_id.items():
            try:
                node_type = NodeType(node.get("type", ""))
                if node_type == NodeType.START:
                    start_nodes.append(nid)
            except ValueError:
                pass

        if not start_nodes:
            logger.warning("No start nodes found in diagram")

        return start_nodes

    def check_dependencies_met(self,
                               node_id: str,
                               executed_nodes: Set[str],
                               condition_values: Dict[str, bool],
                               context: Dict[str, Any]) -> Tuple[bool, List[dict]]:
        """Check if all dependencies for a node are met."""
        node = self.nodes_by_id[node_id]
        logger.debug(f"\n[Dependency Check] Node {node_id} (type: {node.get('type')})")

        # Start nodes have no dependencies
        if self._is_start_node(node):
            return True, []

        incoming_arrows = self.incoming_arrows.get(node_id, [])
        logger.debug(f"[Dependency Check] Incoming arrows: {len(incoming_arrows)}")
        if not incoming_arrows:
            return True, []

        # Validate each incoming arrow
        arrow_validations = [
            self._validate_arrow_dependency(arrow, node_id, context, condition_values)
            for arrow in incoming_arrows
        ]

        valid_arrows = [v.arrow for v in arrow_validations if v.is_valid]
        missing_deps = [v.arrow for v in arrow_validations if not v.is_valid]

        # Special handling for PersonJob nodes with first-only inputs
        if self._can_execute_with_first_only(node, node_id, incoming_arrows, context):
            logger.debug(f"[Dependency Check] PersonJobNode {node_id} can execute with first_only input")
            # Return all first-only arrows that have data available
            first_only_arrows = []
            for arrow in incoming_arrows:
                if self._is_handle_first_only(arrow):
                    src_id = ArrowUtils.get_source(arrow)
                    if src_id and src_id in context:
                        first_only_arrows.append(arrow)
            return True, first_only_arrows

        dependencies_met = len(missing_deps) == 0
        return dependencies_met, valid_arrows

    def _is_start_node(self, node: dict) -> bool:
        """Check if node is a start node."""
        return node.get("type") == NodeType.START.value

    def _get_node_type(self, node: dict) -> Optional[NodeType]:
        """Safely get node type."""
        try:
            return NodeType(node.get("type", ""))
        except ValueError:
            return None

    def _is_handle_first_only(self, arrow: dict) -> bool:
        """Check if arrow uses first-only handle mode."""
        target_handle = arrow.get("targetHandle") or ""
        if target_handle.endswith("-input-first"):
            return True
        return arrow.get("data", {}).get("handleMode", "default") == "first_only"

    def _validate_arrow_dependency(self, 
                                   arrow: dict, 
                                   target_node_id: str,
                                   context: Dict[str, Any],
                                   condition_values: Dict[str, bool]) -> ArrowValidation:
        """Validate a single arrow dependency."""
        src_id = ArrowUtils.get_source(arrow)
        if not src_id:
            return ArrowValidation(is_valid=False, arrow=arrow, reason="no_source")

        logger.debug(f"[Dependency Check] arrow from {src_id} -> {target_node_id}")
        
        # Get source node info
        src_node = self.nodes_by_id.get(src_id, {})
        src_type = self._get_node_type(src_node)
        is_start_source = src_type == NodeType.START
        is_condition_source = src_type == NodeType.CONDITION
        has_data = src_id in context

        # Handle first-only mode
        if self._is_handle_first_only(arrow):
            return self._validate_first_only_arrow(arrow, target_node_id, has_data)

        # Handle regular dependencies
        if not has_data and src_id != target_node_id and not is_start_source:
            return ArrowValidation(is_valid=False, arrow=arrow, reason="missing_data")

        # Handle condition branches
        if is_condition_source:
            return self._validate_condition_branch(arrow, src_id, condition_values)

        return ArrowValidation(is_valid=True, arrow=arrow)

    def _validate_first_only_arrow(self, arrow: dict, target_node_id: str, has_data: bool) -> ArrowValidation:
        """Validate first-only handle mode arrow."""
        if not self.first_only_consumed.get(target_node_id, False):
            # First-only not consumed yet - valid if has data
            if has_data:
                return ArrowValidation(is_valid=True, arrow=arrow)
            return ArrowValidation(is_valid=False, arrow=arrow, reason="first_only_no_data")
        else:
            # First-only already consumed - always valid
            return ArrowValidation(is_valid=True, arrow=arrow)

    def _validate_condition_branch(self, arrow: dict, src_id: str, condition_values: Dict[str, bool]) -> ArrowValidation:
        """Validate condition node branch."""
        branch = self._extract_branch_from_arrow(arrow)
        if not branch:
            return ArrowValidation(is_valid=True, arrow=arrow)

        if src_id not in condition_values:
            return ArrowValidation(is_valid=False, arrow=arrow, reason="condition_not_evaluated")

        cond_value = condition_values[src_id]
        if (branch == "true" and not cond_value) or (branch == "false" and cond_value):
            return ArrowValidation(is_valid=False, arrow=arrow, reason="wrong_branch")

        return ArrowValidation(is_valid=True, arrow=arrow)

    def _extract_branch_from_arrow(self, arrow: dict) -> Optional[str]:
        """Extract branch information from arrow sourceHandle or data."""
        # First check if branch is explicitly set in data
        branch = arrow.get("data", {}).get("branch")
        if branch:
            return branch
        
        # Check label field
        label = arrow.get("data", {}).get("label", "")
        if label.lower() in ["true", "false"]:
            return label.lower()
            
        # Extract from sourceHandle (e.g., "conditionNode-WPKS8Q-output-true" -> "true")
        source_handle = arrow.get("sourceHandle") or ""
        if source_handle.endswith("-output-true"):
            return "true"
        elif source_handle.endswith("-output-false"):
            return "false"
            
        return None

    def _can_execute_with_first_only(self, 
                                     node: dict, 
                                     node_id: str,
                                     incoming_arrows: List[dict],
                                     context: Dict[str, Any]) -> bool:
        """Check if PersonJob node can execute with just first-only inputs."""
        node_type = self._get_node_type(node)
        if node_type != NodeType.PERSON_JOB:
            return False

        if self.first_only_consumed.get(node_id, False):
            return False

        # Check if any first-only input has data
        for arrow in incoming_arrows:
            if self._is_handle_first_only(arrow):
                src_id = ArrowUtils.get_source(arrow)
                if src_id and src_id in context:
                    return True

        return False

    def get_next_nodes(self, node_id: str, condition_values: Dict[str, bool]) -> List[str]:
        """Get the next nodes to execute after a given node."""
        outgoing = self.outgoing_arrows.get(node_id, [])
        next_nodes = []

        for arrow in outgoing:
            target_id = ArrowUtils.get_target(arrow)
            if not target_id:
                continue

            # Check condition branches
            src_node = self.nodes_by_id.get(node_id, {})
            if self._get_node_type(src_node) == NodeType.CONDITION:
                branch = self._extract_branch_from_arrow(arrow)
                if branch:
                    cond_value = condition_values.get(node_id, False)
                    if (branch == "true" and not cond_value) or (branch == "false" and cond_value):
                        continue

            next_nodes.append(target_id)

        return next_nodes

    def create_execution_plan(self) -> Dict[str, Any]:
        """Create execution plan with validation and metadata."""
        start_nodes = self.validate_start_nodes()
        cycles = self._detect_cycles()

        return {
            "start_nodes": start_nodes,
            "has_cycles": len(cycles) > 0,
            "cycle_nodes": cycles,
            "total_nodes": len(self.nodes),
            "total_arrows": len(self.arrows),
            "node_types": {n["id"]: n.get("type", "unknown") for n in self.nodes}
        }

    def _detect_cycles(self) -> List[List[str]]:
        """Detect cycles in the graph using DFS."""
        cycles = []
        visited = set()
        rec_stack = set()

        def dfs(node_id: str, path: List[str]) -> None:
            visited.add(node_id)
            rec_stack.add(node_id)
            path.append(node_id)

            for arrow in self.outgoing_arrows.get(node_id, []):
                neighbor = ArrowUtils.get_target(arrow)
                if neighbor in rec_stack:
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)
                elif neighbor not in visited:
                    dfs(neighbor, path.copy())

            rec_stack.remove(node_id)

        for node_id in self.nodes_by_id:
            if node_id not in visited:
                dfs(node_id, [])

        return cycles
    
    def mark_first_only_consumed(self, node_id: str) -> None:
        """Mark that a node has consumed its first-only inputs."""
        self.first_only_consumed[node_id] = True
    
    def reset_first_only_consumed(self, node_id: str) -> None:
        """Reset first-only consumed status for a node (used in loops)."""
        if node_id in self.first_only_consumed:
            del self.first_only_consumed[node_id]