from typing import Dict, Set, Any, Optional, Tuple
import re
import logging
from enum import Enum

logger = logging.getLogger(__name__)


class SkipReason(Enum):
    """Enumeration of skip reasons"""
    MAX_ITERATIONS_REACHED = "max_iterations_reached"
    CONDITION_NOT_MET = "condition_not_met"
    DEPENDENCY_SKIPPED = "dependency_skipped"
    USER_REQUESTED = "user_requested"
    ERROR_IN_DEPENDENCY = "error_in_dependency"
    FIRST_ONLY_CONSUMED = "first_only_consumed"


class SkipManager:
    """
    Centralizes skip decision logic, tracking which nodes should be skipped
    and why during execution.
    """
    
    def __init__(self):
        self.skip_reasons: Dict[str, str] = {}
        self.skipped_nodes: Set[str] = set()
        self.logger = logger
    
    def should_skip(self, node: Dict[str, Any], context: 'ExecutionContext') -> bool:
        """
        Main skip decision based on various factors.
        
        Args:
            node: The node to evaluate
            context: Current execution context
            
        Returns:
            True if the node should be skipped
        """
        node_id = node["id"]
        
        # Check if already skipped
        if node_id in self.skipped_nodes:
            return True
        
        # Check iteration-based skip
        if self._should_skip_due_to_iterations(node, context):
            self.mark_skipped(node_id, SkipReason.MAX_ITERATIONS_REACHED.value)
            return True
        
        # Check condition-based skip
        skip_due_to_condition, reason = self._should_skip_based_on_condition(node, context)
        if skip_due_to_condition:
            self.mark_skipped(node_id, reason)
            return True
        
        # Check dependency-based skip
        if self._should_skip_due_to_dependencies(node, context):
            self.mark_skipped(node_id, SkipReason.DEPENDENCY_SKIPPED.value)
            return True
        
        # Check first-only consumption for PersonJob nodes
        if self._should_skip_due_to_first_only(node, context):
            self.mark_skipped(node_id, SkipReason.FIRST_ONLY_CONSUMED.value)
            return True
        
        return False
    
    def _should_skip_due_to_iterations(self, node: Dict[str, Any], context: 'ExecutionContext') -> bool:
        """Check if node should skip due to max iterations"""
        node_id = node["id"]
        properties = node.get("properties", {})
        
        # Check if node has max_iterations property
        max_iterations = properties.get("max_iterations")
        if max_iterations is not None and isinstance(max_iterations, int):
            current_count = context.node_execution_counts.get(node_id, 0)
            if current_count >= max_iterations:
                self.logger.info(f"Node {node_id} reached max iterations: {max_iterations}")
                return True
        
        return False
    
    def _should_skip_due_to_dependencies(self, node: Dict[str, Any], context: 'ExecutionContext') -> bool:
        """Check if node should skip because dependencies were skipped"""
        node_id = node["id"]
        
        # Get all dependencies
        incoming_arrows = context.incoming_arrows.get(node_id, [])
        
        # Check if all non-optional dependencies were skipped
        required_deps_skipped = True
        has_required_deps = False
        
        for arrow in incoming_arrows:
            source_id = arrow["source"]
            
            # Skip if source doesn't exist
            if source_id not in context.nodes_by_id:
                continue
            
            # Check if this is an optional dependency (first-only)
            is_optional = self._is_optional_dependency(arrow, node)
            
            if not is_optional:
                has_required_deps = True
                if source_id not in context.skipped_nodes:
                    required_deps_skipped = False
                    break
        
        # Skip only if we have required dependencies and all were skipped
        return has_required_deps and required_deps_skipped
    
    def _should_skip_due_to_first_only(self, node: Dict[str, Any], context: 'ExecutionContext') -> bool:
        """Check if PersonJob should skip because first-only was already consumed"""
        if node["type"] not in ["personjob", "personbatchjob"]:
            return False
        
        node_id = node["id"]
        properties = node.get("properties", {})
        
        # Check if node has first-only configuration
        if properties.get("firstOnlyPrompt") and context.first_only_consumed.get(node_id, False):
            # Already consumed first-only and no default prompt
            if not properties.get("defaultPrompt"):
                return True
        
        return False
    
    def _is_optional_dependency(self, arrow: Dict[str, Any], target_node: Dict[str, Any]) -> bool:
        """Check if an arrow represents an optional (first-only) dependency"""
        if target_node["type"] in ["personjob", "personbatchjob"]:
            properties = target_node.get("properties", {})
            first_only_inputs = properties.get("firstOnlyInputs", [])
            arrow_label = arrow.get("label", "")
            return arrow_label in first_only_inputs
        return False
    
    def evaluateCondition(self, expression: str, context: Dict[str, Any]) -> bool:
        """
        Evaluate a condition expression with context.
        Supports simple comparisons and logical operators.
        
        Args:
            expression: The condition expression to evaluate
            context: Variable context for substitution
            
        Returns:
            Boolean result of the evaluation
        """
        try:
            # Substitute variables in the expression
            substituted = self._substitute_variables(expression, context)
            
            # Simple expression evaluation
            # WARNING: This is a simplified version. In production, use a proper expression parser
            result = self._evaluate_simple_expression(substituted)
            
            return bool(result)
        except Exception as e:
            self.logger.error(f"Failed to evaluate condition '{expression}': {e}")
            return False
    
    def _substitute_variables(self, expression: str, context: Dict[str, Any]) -> str:
        """Substitute variables in expression"""
        # Pattern for {{variable}} or ${variable}
        pattern = r'\{\{(\w+)\}\}|\$\{(\w+)\}'
        
        def replace_var(match):
            var_name = match.group(1) or match.group(2)
            value = context.get(var_name, f"undefined_{var_name}")
            # Convert to string representation suitable for evaluation
            if isinstance(value, str):
                return f'"{value}"'
            elif isinstance(value, bool):
                return "True" if value else "False"
            elif value is None:
                return "None"
            else:
                return str(value)
        
        return re.sub(pattern, replace_var, expression)
    
    def _evaluate_simple_expression(self, expression: str) -> Any:
        """
        Evaluate a simple expression safely.
        Only supports basic comparisons and logical operators.
        """
        # Remove extra whitespace
        expression = expression.strip()
        
        # Handle boolean literals
        if expression.lower() == "true":
            return True
        elif expression.lower() == "false":
            return False
        
        # Handle basic comparisons
        # This is a simplified implementation - enhance with proper parsing
        operators = ["===", "!==", "==", "!=", ">=", "<=", ">", "<"]
        
        for op in operators:
            if op in expression:
                parts = expression.split(op, 1)
                if len(parts) == 2:
                    left = self._parse_value(parts[0].strip())
                    right = self._parse_value(parts[1].strip())
                    
                    if op in ["===", "=="]:
                        return left == right
                    elif op in ["!==", "!="]:
                        return left != right
                    elif op == ">=":
                        return float(left) >= float(right)
                    elif op == "<=":
                        return float(left) <= float(right)
                    elif op == ">":
                        return float(left) > float(right)
                    elif op == "<":
                        return float(left) < float(right)
        
        # Handle logical operators (simplified)
        if "&&" in expression:
            parts = expression.split("&&")
            return all(self._evaluate_simple_expression(p.strip()) for p in parts)
        elif "||" in expression:
            parts = expression.split("||")
            return any(self._evaluate_simple_expression(p.strip()) for p in parts)
        
        # Try to parse as a simple value
        return self._parse_value(expression)
    
    def _parse_value(self, value: str) -> Any:
        """Parse a string value into appropriate type"""
        value = value.strip()
        
        # Handle quoted strings
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            return value[1:-1]
        
        # Handle booleans
        if value.lower() == "true":
            return True
        elif value.lower() == "false":
            return False
        
        # Handle None/null
        if value.lower() in ["none", "null"]:
            return None
        
        # Try to parse as number
        try:
            if "." in value:
                return float(value)
            else:
                return int(value)
        except ValueError:
            # Return as string if all else fails
            return value
    
    def markSkipped(self, node_id: str, reason: str) -> None:
        """
        Record a node as skipped with reason.
        
        Args:
            node_id: The node that was skipped
            reason: Why it was skipped
        """
        self.skipped_nodes.add(node_id)
        self.skip_reasons[node_id] = reason
        self.logger.info(f"Node {node_id} skipped: {reason}")
    
    def isSkipped(self, node_id: str) -> bool:
        """
        Check if a node was skipped.
        
        Args:
            node_id: The node to check
            
        Returns:
            True if the node was skipped
        """
        return node_id in self.skipped_nodes
    
    def getSkipReason(self, node_id: str) -> Optional[str]:
        """
        Get the reason why a node was skipped.
        
        Args:
            node_id: The node to check
            
        Returns:
            Skip reason or None if not skipped
        """
        return self.skip_reasons.get(node_id)
    
    def get_skip_reason(self, node_id: str) -> Optional[str]:
        """Alias for getSkipReason for consistency"""
        return self.getSkipReason(node_id)
    
    def shouldSkipBasedOnCondition(
        self, 
        node: Dict[str, Any], 
        context: 'ExecutionContext'
    ) -> Tuple[bool, str]:
        """
        Check if node should skip based on condition evaluation.
        
        Args:
            node: The node to evaluate
            context: Execution context
            
        Returns:
            Tuple of (should_skip, reason)
        """
        return self._should_skip_based_on_condition(node, context)
    
    def _should_skip_based_on_condition(
        self,
        node: Dict[str, Any],
        context: 'ExecutionContext'
    ) -> Tuple[bool, str]:
        """Internal method for condition-based skip logic"""
        node_type = node.get("type")
        properties = node.get("properties", {})
        
        # Special handling for condition nodes checking max_iterations
        if node_type == "condition":
            condition_type = properties.get("conditionType")
            if condition_type == "max_iterations":
                # This condition should return true when all nodes reach max iterations
                # (handled by the executor, not skip logic)
                return False, ""
        
        # Check skip conditions in node properties
        skip_condition = properties.get("skipCondition")
        if skip_condition:
            # Build context for condition evaluation
            eval_context = {
                "node_outputs": context.node_outputs,
                "execution_counts": context.node_execution_counts,
                **context.node_outputs  # Flatten outputs for easier access
            }
            
            should_skip = self.evaluateCondition(skip_condition, eval_context)
            if should_skip:
                return True, SkipReason.CONDITION_NOT_MET.value
        
        return False, ""
    
    def getAllSkippedNodes(self) -> Dict[str, str]:
        """
        Get all skipped nodes and their reasons.
        
        Returns:
            Dictionary mapping node IDs to skip reasons
        """
        return dict(self.skip_reasons)