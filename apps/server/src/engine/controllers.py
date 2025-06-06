from typing import Dict, Set, List, Optional, Tuple, Any
from dataclasses import dataclass, field
import logging
from enum import Enum

from .executors.utils import substitute_variables

logger = logging.getLogger(__name__)


@dataclass
class IterationStats:
    """Statistics about loop iterations."""
    total_iterations: Dict[str, int] = field(default_factory=dict)
    max_iterations_map: Dict[str, int] = field(default_factory=dict)
    nodes_at_max: Set[str] = field(default_factory=set)
    all_nodes_at_max: bool = False


class SkipReason(Enum):
    """Enumeration of skip reasons."""
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    CONDITION_NOT_MET = "condition_not_met"
    DEPENDENCY_SKIPPED = "dependency_skipped"
    USER_REQUESTED = "user_requested"
    ERROR_IN_DEPENDENCY = "error_in_dependency"
    FIRST_ONLY_CONSUMED = "first_only_consumed"


class LoopController:
    """
    Manages loop execution state, tracking iterations for nodes and
    determining when loops should terminate.
    """

    def __init__(self, max_iterations: int = 100):
        """
        Initialize loop controller.

        Args:
            max_iterations: Global maximum iteration limit for safety.
        """
        # iteration_counts defaults to 0 for any new node
        self.iteration_counts: Dict[str, int] = {}
        self.max_iterations = max_iterations
        self.loop_nodes: Set[str] = set()
        self.node_max_iterations: Dict[str, int] = {}
        self.logger = logger

    def register_loop_node(self, node_id: str, max_iterations: Optional[int] = None) -> None:
        """
        Register a node as part of a loop with optional max iterations.

        Args:
            node_id: The node ID to register.
            max_iterations: Node-specific max iterations (overrides global limit).
        """
        self.loop_nodes.add(node_id)
        if max_iterations is not None:
            self.node_max_iterations[node_id] = max_iterations

        # Ensure there's an entry (defaults to 0)
        self.iteration_counts.setdefault(node_id, 0)

    def _effective_max(self, node_id: str) -> int:
        """
        Return the "effective" max-iteration count for a node:
        either the per-node override (if present), or the global max.
        """
        return self.node_max_iterations.get(node_id, self.max_iterations)

    def should_continue_loop(self, node_id: str) -> bool:
        """
        Check if a node should continue iterating.

        Args:
            node_id: The node to check.

        Returns:
            True if the node should continue, False if it should stop.
        """
        # If this node never registered as a loop node, we assume "always continue"
        if node_id not in self.loop_nodes:
            return True

        current = self.iteration_counts.get(node_id, 0)
        limit = self._effective_max(node_id)

        if current >= limit:
            # Distinguish logging based on whether it was node-specific vs. global
            if node_id in self.node_max_iterations:
                self.logger.debug(f"Node {node_id} reached its own max iterations: {limit}")
            else:
                self.logger.warning(f"Node {node_id} reached global max iterations: {limit}")
            return False

        return True

    def increment_iteration(self, node_id: str) -> int:
        """
        Increment iteration count for a node.

        Args:
            node_id: The node to increment.

        Returns:
            The new iteration count.
        """
        self.iteration_counts[node_id] = self.iteration_counts.get(node_id, 0) + 1
        return self.iteration_counts[node_id]

    def reset_iterations(self, node_id: str) -> None:
        """
        Reset iteration count for a node.

        Args:
            node_id: The node to reset.
        """
        self.iteration_counts[node_id] = 0
        self.logger.debug(f"Reset iterations for node {node_id}")

    def get_iteration_count(self, node_id: str) -> int:
        """
        Get current iteration count for a node (0-based).

        Args:
            node_id: The node to check.

        Returns:
            Current iteration count (0 if never executed).
        """
        return self.iteration_counts.get(node_id, 0)

    def get_remaining_iterations(self, node_id: str) -> Optional[int]:
        """
        Calculate remaining iterations for a node.

        Args:
            node_id: The node to check.

        Returns:
            Number of remaining iterations, or 0 if already at/beyond limit.
        """
        current = self.get_iteration_count(node_id)
        limit = self._effective_max(node_id)
        return max(0, limit - current)

    def has_any_node_reached_max_iterations(self) -> bool:
        """
        Check if ANY loop-registered node has reached its max iteration limit.

        Returns:
            True if any node is at or beyond its limit.
        """
        # Equivalent to: is there at least one node_id such that current >= effective_max
        return any(
            self.iteration_counts.get(nid, 0) >= self._effective_max(nid)
            for nid in self.loop_nodes
        )

    def have_all_nodes_reached_max_iterations(self) -> bool:
        """
        Check if ALL loop-registered nodes have reached their max iteration limits.
        (Used by a condition node to decide loop termination.)

        Returns:
            True if every loop node is at or beyond its limit, False otherwise.
            If there are no loop nodes, returns False.
        """
        if not self.loop_nodes:
            return False

        return all(
            self.iteration_counts.get(nid, 0) >= self._effective_max(nid)
            for nid in self.loop_nodes
        )

    def get_iteration_stats(self) -> IterationStats:
        """
        Get comprehensive iteration statistics.

        Returns:
            IterationStats object with total counts, effective maxes, and which nodes are capped.
        """
        stats = IterationStats()

        for nid in self.loop_nodes:
            curr = self.iteration_counts.get(nid, 0)
            eff_max = self._effective_max(nid)

            stats.total_iterations[nid] = curr
            stats.max_iterations_map[nid] = eff_max

            if curr >= eff_max:
                stats.nodes_at_max.add(nid)

        stats.all_nodes_at_max = bool(
            self.loop_nodes and len(stats.nodes_at_max) == len(self.loop_nodes)
        )
        return stats

    def mark_iteration_complete(self, node_id: str) -> Tuple[bool, int]:
        """
        Mark an iteration as complete for a node (increment count, then decide continuation).

        Args:
            node_id: The node that completed an iteration.

        Returns:
            (should_continue: bool, new_iteration_count: int)
        """
        new_count = self.increment_iteration(node_id)
        return (new_count < self._effective_max(node_id), new_count)

    def create_sub_controller(self, node_ids: List[str]) -> 'LoopController':
        """
        Create a new LoopController for a subset of nodes (e.g., nested loops).

        Args:
            node_ids: List of node IDs to carry over.

        Returns:
            A newly instantiated LoopController sharing the same global max.
        """
        sub = LoopController(max_iterations=self.max_iterations)
        for nid in node_ids:
            if nid in self.loop_nodes:
                # Copy over per-node override if it exists
                sub.register_loop_node(nid, self.node_max_iterations.get(nid))
        return sub

    def update_from_node_properties(self, node: Dict[str, Any]) -> None:
        """
        Update loop configuration from a node's properties (e.g., PersonJob with maxIteration).

        Args:
            node: Node dictionary containing keys "id", "type", and optional "properties".
        """
        node_id = node.get("id")
        props = node.get("properties", {})
        # If node explicitly supplies a maxIteration integer > 0, register with that override
        max_iter = props.get("maxIteration")
        if isinstance(max_iter, int) and max_iter > 0:
            self.register_loop_node(node_id, max_iter)
            self.logger.debug(f"Registered loop node {node_id} with maxIteration={max_iter}")
            return

        # Otherwise, if node-type indicates a PersonJob or PersonBatchJob and it has loop indicators, register with no override
        node_type = (node.get("type") or "").lower()
        if node_type in {"personjob", "personbatchjob"}:
            if props.get("firstOnlyPrompt") or props.get("iterationPrompt"):
                self.register_loop_node(node_id)
                self.logger.debug(f"Registered {node_type} node {node_id} as loop node")


class SkipManager:
    """
    Centralizes skip‐decision logic, tracking which nodes should be skipped and why.
    """

    def __init__(self):
        self.skip_reasons: Dict[str, str] = {}
        self.skipped_nodes: Set[str] = set()
        self.logger = logger

    def should_skip(self, node: Dict[str, Any], context: 'ExecutionContext') -> bool:
        """
        Main skip decision based on multiple factors:
        1) Already marked skipped
        2) Exceeded iteration count (PersonJob-type)
        3) skipCondition property
        4) Dependencies all skipped
        5) firstOnlyPrompt already consumed

        Args:
            node: The node to evaluate (must have "id", "type", "properties").
            context: Current execution context (must expose node_execution_counts, incoming_arrows, skipped_nodes, first_only_consumed, node_outputs).

        Returns:
            True if the node should be skipped, False otherwise. If skipped, records a reason.
        """
        node_id = node["id"]
        if node_id in self.skipped_nodes:
            return True

        # 1) Iteration-based skip (only PersonJob-like nodes)
        if self._skip_due_to_iterations(node, context):
            self.mark_skipped(node_id, SkipReason.MAX_ITERATIONS_REACHED.value)
            return True

        # 2) Condition-based skip (skipCondition property)
        skip_cond, reason = self._skip_based_on_condition(node, context)
        if skip_cond:
            self.mark_skipped(node_id, reason)
            return True

        # 3) Dependency-based skip (all required deps were skipped)
        if self._skip_due_to_dependencies(node, context):
            self.mark_skipped(node_id, SkipReason.DEPENDENCY_SKIPPED.value)
            return True

        # 4) firstOnlyPrompt‐based skip (only PersonJob-type)
        if self._skip_due_to_first_only(node, context):
            self.mark_skipped(node_id, SkipReason.FIRST_ONLY_CONSUMED.value)
            return True

        return False

    def _normalize_node_type(self, node: Dict[str, Any]) -> str:
        """
        Return lowercase of either node["properties"]["type"] if present, or node["type"].
        This helps unify checks for PersonJob-like nodes.
        """
        props = node.get("properties", {})
        # Use .get("type") inside properties if available, else top-level
        return (props.get("type", node.get("type", "")) or "").lower()

    def _is_personjob_type(self, node: Dict[str, Any]) -> bool:
        """
        Return True if this node is one of the recognized PersonJob-like types.
        """
        nt = self._normalize_node_type(node)
        return nt in {
            "personjob",
            "person_job",
            "personbatchjob",
            "person_batch_job"
        }

    def _skip_due_to_iterations(self, node: Dict[str, Any], context: 'ExecutionContext') -> bool:
        """
        Skip if a PersonJob-type node has a 'maxIteration' property
        and its execution count has been exhausted.
        """
        if not self._is_personjob_type(node):
            return False

        node_id = node["id"]
        props = node.get("properties", {})
        max_iter = props.get("maxIteration")
        if isinstance(max_iter, int):
            current_count = context.node_execution_counts.get(node_id, 0)
            if current_count >= max_iter:
                self.logger.debug(f"Node {node_id} reached max iterations: {max_iter}")
                return True

        return False

    def _skip_due_to_dependencies(self, node: Dict[str, Any], context: 'ExecutionContext') -> bool:
        """
        Skip if all required (non-optional) upstream dependencies were skipped.
        Optional dependencies are those labeled in 'firstOnlyInputs'.
        """
        node_id = node["id"]
        incoming = context.incoming_arrows.get(node_id, [])
        props = node.get("properties", {})
        first_only_inputs = set(props.get("firstOnlyInputs", []))

        has_required = False
        all_required_skipped = True

        for arrow in incoming:
            source_id = arrow.get("source")
            if source_id not in context.nodes_by_id:
                # If the source doesn't exist in the graph, ignore it.
                continue

            is_optional = arrow.get("label", "") in first_only_inputs
            if not is_optional:
                has_required = True
                if source_id not in context.skipped_nodes:
                    all_required_skipped = False
                    break

        return has_required and all_required_skipped

    def _skip_due_to_first_only(self, node: Dict[str, Any], context: 'ExecutionContext') -> bool:
        """
        Skip PersonJob-type nodes if 'firstOnlyPrompt' was consumed previously and
        there is no 'defaultPrompt' to fall back on.
        """
        if not self._is_personjob_type(node):
            return False

        node_id = node["id"]
        props = node.get("properties", {})
        if props.get("firstOnlyPrompt") and context.first_only_consumed.get(node_id, False):
            if not props.get("defaultPrompt"):
                return True

        return False

    def _skip_based_on_condition(self, node: Dict[str, Any], context: 'ExecutionContext') -> Tuple[bool, str]:
        """
        Evaluate a skipCondition expression in node properties (if any).
        Returns (True, reason) if skipCondition evaluates to True; else (False, "").
        """
        props = node.get("properties", {})
        skip_expr = props.get("skipCondition")
        if not skip_expr:
            return (False, "")

        # Build an evaluation context by merging node_outputs and execution_counts
        eval_context = {
            "node_outputs": context.node_outputs,
            "execution_counts": context.node_execution_counts,
            **context.node_outputs,  # flatten all outputs for easy access
        }

        if self._evaluate_condition(skip_expr, eval_context):
            return (True, SkipReason.CONDITION_NOT_MET.value)
        return (False, "")

    def _evaluate_condition(self, expression: str, context: Dict[str, Any]) -> bool:
        """
        1) Substitute variables
        2) Evaluate a simple boolean/comparison expression
        """
        try:
            substituted = substitute_variables(expression, context, evaluation_mode=True)
            return bool(self._evaluate_simple_expression(substituted))
        except Exception as e:
            self.logger.error(f"Failed to evaluate condition '{expression}': {e}")
            return False

    def _evaluate_simple_expression(self, expr: str) -> Any:
        """
        A minimal parser for:
          - boolean literals true/false
          - comparisons: ==, !=, >=, <=, >, <
          - logical &&, ||
        Does NOT use eval() and is purely string-based.
        """
        expression = expr.strip()

        # Boolean literals
        low = expression.lower()
        if low == "true":
            return True
        if low == "false":
            return False

        # Comparison operators
        for op in ("===", "!==", "==", "!=", ">=", "<=", ">", "<"):
            if op in expression:
                left, right = expression.split(op, 1)
                left_val = self._parse_value(left.strip())
                right_val = self._parse_value(right.strip())
                if op in ("===", "=="):
                    return left_val == right_val
                if op in ("!==", "!="):
                    return left_val != right_val
                if op == ">=":
                    return float(left_val) >= float(right_val)
                if op == "<=":
                    return float(left_val) <= float(right_val)
                if op == ">":
                    return float(left_val) > float(right_val)
                if op == "<":
                    return float(left_val) < float(right_val)

        # Logical AND/OR
        if "&&" in expression:
            return all(self._evaluate_simple_expression(part.strip()) for part in expression.split("&&"))
        if "||" in expression:
            return any(self._evaluate_simple_expression(part.strip()) for part in expression.split("||"))

        # Fallback: plain value
        return self._parse_value(expression)

    def _parse_value(self, value: str) -> Any:
        """
        Convert a string literal into Python types: number, boolean, None, or stripped string.
        """
        v = value.strip()
        if (v.startswith("'") and v.endswith("'")) or (v.startswith('"') and v.endswith('"')):
            return v[1:-1]
        low = v.lower()
        if low == "true":
            return True
        if low == "false":
            return False
        if low in ("none", "null"):
            return None

        # Try numeric
        try:
            if "." in v:
                return float(v)
            return int(v)
        except ValueError:
            return v

    def mark_skipped(self, node_id: str, reason: str) -> None:
        """
        Record a node as skipped with a reason.
        """
        self.skipped_nodes.add(node_id)
        self.skip_reasons[node_id] = reason
        self.logger.debug(f"Node {node_id} skipped: {reason}")

    def is_skipped(self, node_id: str) -> bool:
        return node_id in self.skipped_nodes

    def get_skip_reason(self, node_id: str) -> Optional[str]:
        return self.skip_reasons.get(node_id)

    def get_all_skipped_nodes(self) -> Dict[str, str]:
        return dict(self.skip_reasons)
