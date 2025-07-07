"""Domain service for evaluating conditions."""

import ast
import operator
from typing import Any, Dict, Optional

from dipeo.models import DomainDiagram, NodeType
from dipeo.domain.domains.text.template_service import TemplateService


class ConditionEvaluationService:
    """Service for evaluating conditions in diagram execution."""
    
    def __init__(self, template_service: TemplateService):
        self._template_service = template_service
    
    def evaluate_max_iterations(
        self,
        diagram: DomainDiagram,
        execution_states: Dict[str, Dict[str, Any]],
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> bool:
        """Evaluate if all upstream person_job nodes reached their max_iterations.
        
        Business logic:
        - Find all person_job nodes in the diagram
        - Check if they have been executed at least once
        - Compare execution count against max_iteration setting
        - Return true only if all executed person_job nodes have reached max
        """
        if not diagram:
            return False
        
        found_person_job = False
        all_reached_max = True
        
        for node in diagram.nodes:
            if node.type == NodeType.person_job.value:
                # Get execution count
                exec_count = 0
                
                # Check if node has been executed
                node_state = execution_states.get(node.id)
                if node_state and node_state.get('status', 'pending') != 'pending':
                    # Node has been executed at least once
                    exec_count = 1
                    
                    # Get actual count from tracking service if available
                    if node_exec_counts and node.id in node_exec_counts:
                        exec_count = node_exec_counts[node.id]
                
                # Only check nodes that have executed at least once
                if exec_count > 0:
                    found_person_job = True
                    max_iter = int((node.data or {}).get("max_iteration", 1))
                    if exec_count < max_iter:
                        all_reached_max = False
                        break
        
        # Return true only if we found at least one person_job AND all have reached max
        return found_person_job and all_reached_max
    
    def evaluate_custom_expression(
        self,
        expression: str,
        context_values: Dict[str, Any],
    ) -> bool:
        """Evaluate a custom boolean expression with variable substitution.
        
        Business logic:
        - Substitute variables in the expression using template service
        - Safely evaluate the resulting expression
        - Return boolean result or False on error
        """
        if not expression:
            return False
        
        # Substitute variables in the expression
        substituted_expr = self._template_service.substitute_template(
            expression, context_values
        )
        
        # Evaluate the expression
        return self.safe_evaluate_expression(substituted_expr)
    
    def safe_evaluate_expression(self, expression: str) -> Any:
        """Safely evaluate a boolean expression.
        
        Business logic:
        - Only allows specific operators for security
        - Parses expression into AST
        - Recursively evaluates AST nodes
        - Returns evaluation result or False on error
        """
        # Define allowed operators
        allowed_operators = {
            ast.Eq: operator.eq,
            ast.NotEq: operator.ne,
            ast.Lt: operator.lt,
            ast.LtE: operator.le,
            ast.Gt: operator.gt,
            ast.GtE: operator.ge,
            ast.And: operator.and_,
            ast.Or: operator.or_,
            ast.Not: operator.not_,
            ast.In: lambda x, y: x in y,
            ast.NotIn: lambda x, y: x not in y,
        }
        
        # Parse the expression
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError:
            return False
        
        # Evaluate the expression tree
        def eval_node(node):
            if isinstance(node, ast.Expression):
                return eval_node(node.body)
            elif isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.Str):  # For Python < 3.8 compatibility
                return node.s
            elif isinstance(node, ast.Num):  # For Python < 3.8 compatibility
                return node.n
            elif isinstance(node, ast.Compare):
                left = eval_node(node.left)
                for op, comparator in zip(node.ops, node.comparators):
                    op_func = allowed_operators.get(type(op))
                    if op_func is None:
                        raise ValueError(f"Unsupported operator: {type(op).__name__}")
                    right = eval_node(comparator)
                    if not op_func(left, right):
                        return False
                    left = right
                return True
            elif isinstance(node, ast.BoolOp):
                op_func = allowed_operators.get(type(node.op))
                if op_func is None:
                    raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
                values = [eval_node(v) for v in node.values]
                if isinstance(node.op, ast.And):
                    return all(values)
                else:  # ast.Or
                    return any(values)
            elif isinstance(node, ast.UnaryOp):
                op_func = allowed_operators.get(type(node.op))
                if op_func is None:
                    raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
                return op_func(eval_node(node.operand))
            else:
                raise ValueError(f"Unsupported node type: {type(node).__name__}")
        
        try:
            return eval_node(tree)
        except Exception:
            return False