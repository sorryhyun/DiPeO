# Condition evaluation service

import ast
import operator
from typing import Any

from dipeo.utils.template import TemplateProcessor
from dipeo.models import DomainDiagram, NodeType


class ConditionEvaluator:
    
    def __init__(self):
        self._processor = TemplateProcessor()
    
    def evaluate_max_iterations(
        self,
        diagram: DomainDiagram,
        execution_states: dict[str, dict[str, Any]],
        node_exec_counts: dict[str, int] | None = None,
    ) -> bool:
        import logging
        logger = logging.getLogger(__name__)
        
        if not diagram:
            return False
        
        found_person_job = False
        all_reached_max = True
        
        logger.debug(f"Evaluating max iterations. Node exec counts: {node_exec_counts}")
        
        for node in diagram.nodes:
            if node.type == NodeType.person_job.value:
                exec_count = 0
                
                node_state = execution_states.get(node.id)
                if node_state and node_state.get('status', 'pending') != 'pending':
                    exec_count = 1
                    
                    if node_exec_counts and node.id in node_exec_counts:
                        exec_count = node_exec_counts[node.id]
                
                if exec_count > 0:
                    found_person_job = True
                    max_iter = int((node.data or {}).get("max_iteration", 1))
                    logger.debug(f"Node {node.id}: exec_count={exec_count}, max_iter={max_iter}")
                    if exec_count < max_iter:
                        all_reached_max = False
                        break
        
        logger.debug(f"Max iterations result: found_person_job={found_person_job}, all_reached_max={all_reached_max}")
        
        return found_person_job and all_reached_max
    
    def check_nodes_executed(
        self,
        target_node_ids: list[str],
        node_outputs: dict[str, Any],
    ) -> bool:
        if not target_node_ids or not node_outputs:
            return False
            
        all_executed = set()
        for output in node_outputs.values():
            if hasattr(output, 'executed_nodes') and output.executed_nodes:
                all_executed.update(output.executed_nodes)
        
        return all(node_id in all_executed for node_id in target_node_ids)
    
    def evaluate_max_iterations_from_outputs(
        self,
        diagram: DomainDiagram,
        node_outputs: dict[str, Any],
        exec_counts: dict[str, int],
    ) -> bool:
        if not diagram or not node_outputs:
            return False
        
        all_executed = set()
        for output in node_outputs.values():
            if hasattr(output, 'executed_nodes') and output.executed_nodes:
                all_executed.update(output.executed_nodes)
        
        found_person_job = False
        all_reached_max = True
        
        for node in diagram.nodes:
            if node.type == NodeType.person_job.value and node.id in all_executed:
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
        if not expression:
            return False
        
        substituted_expr = self._processor.process_simple(expression, context_values)
        
        return self.safe_evaluate_expression(substituted_expr)
    
    def safe_evaluate_expression(self, expression: str) -> Any:
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
        
        try:
            tree = ast.parse(expression, mode='eval')
        except SyntaxError:
            return False
        
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