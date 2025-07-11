# Domain service for evaluating conditions.

import ast
import operator
from typing import Any

from dipeo.utils.template import TemplateProcessor
from dipeo.models import DomainDiagram, NodeType


class ConditionEvaluator:
    # Service for evaluating conditions in diagram execution.
    
    def __init__(self):
        # Initialize with TemplateProcessor.
        self._processor = TemplateProcessor()
    
    def evaluate_max_iterations(
        self,
        diagram: DomainDiagram,
        execution_states: dict[str, dict[str, Any]],
        node_exec_counts: dict[str, int] | None = None,
    ) -> bool:
        # Evaluate if all upstream person_job nodes reached their max_iterations.
        import logging
        logger = logging.getLogger(__name__)
        
        if not diagram:
            return False
        
        found_person_job = False
        all_reached_max = True
        
        logger.debug(f"Evaluating max iterations. Node exec counts: {node_exec_counts}")
        
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
                    logger.debug(f"Node {node.id}: exec_count={exec_count}, max_iter={max_iter}")
                    if exec_count < max_iter:
                        all_reached_max = False
                        break
        
        logger.debug(f"Max iterations result: found_person_job={found_person_job}, all_reached_max={all_reached_max}")
        
        # Return true only if we found at least one person_job AND all have reached max
        return found_person_job and all_reached_max
    
    def check_nodes_executed(
        self,
        target_node_ids: list[str],
        node_outputs: dict[str, Any],
    ) -> bool:
        # Check if specific nodes have been executed using NodeOutput data.
        if not target_node_ids or not node_outputs:
            return False
            
        # Get the most recent output with executed_nodes info
        all_executed = set()
        for output in node_outputs.values():
            if hasattr(output, 'executed_nodes') and output.executed_nodes:
                all_executed.update(output.executed_nodes)
        
        # Check if all target nodes have been executed
        return all(node_id in all_executed for node_id in target_node_ids)
    
    def evaluate_max_iterations_from_outputs(
        self,
        diagram: DomainDiagram,
        node_outputs: dict[str, Any],
        exec_counts: dict[str, int],
    ) -> bool:
        # Evaluate max iterations using NodeOutput data directly.
        if not diagram or not node_outputs:
            return False
        
        # Collect all executed nodes from outputs
        all_executed = set()
        for output in node_outputs.values():
            if hasattr(output, 'executed_nodes') and output.executed_nodes:
                all_executed.update(output.executed_nodes)
        
        # Find person_job nodes and check their status
        found_person_job = False
        all_reached_max = True
        
        for node in diagram.nodes:
            if node.type == NodeType.person_job.value and node.id in all_executed:
                # Only check nodes that have been executed
                found_person_job = True
                exec_count = exec_counts.get(node.id, 0)
                max_iter = int((node.data or {}).get("max_iteration", 1))
                
                if exec_count < max_iter:
                    all_reached_max = False
                    break
        
        return found_person_job and all_reached_max
    
    def evaluate_custom_expression(
        self,
        expression: str,
        context_values: dict[str, Any],
    ) -> bool:
        # Evaluate a custom boolean expression with variable substitution.
        if not expression:
            return False
        
        # Substitute variables in the expression using new processor
        substituted_expr = self._processor.process_simple(expression, context_values)
        
        # Evaluate the expression
        return self.safe_evaluate_expression(substituted_expr)
    
    def safe_evaluate_expression(self, expression: str) -> Any:
        # Safely evaluate a boolean expression.
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
                for op, comparator in zip(node.ops, node.comparators, strict=False):
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