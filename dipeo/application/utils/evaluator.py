# Condition evaluation service

import ast
import operator
from typing import Any

from dipeo.models import DomainDiagram, NodeType
from dipeo.application.utils.template import TemplateProcessor


class ConditionEvaluator:
    
    def __init__(self):
        self._processor = TemplateProcessor()

    
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

    
    def evaluate_custom_expression(
        self,
        expression: str,
        context_values: dict[str, Any],
    ) -> bool:
        if not expression:
            return False
        
        # Debug logging
        import logging
        logger = logging.getLogger(__name__)
        logger.debug(f"evaluate_custom_expression: expression='{expression}'")
        logger.debug(f"evaluate_custom_expression: context_values={context_values}")
        
        # Use a version that supports variable lookups
        return self.safe_evaluate_expression_with_context(expression, context_values)
    
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
    
    def safe_evaluate_expression_with_context(self, expression: str, context: dict[str, Any]) -> Any:
        # Define allowed operators (same as before)
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
            elif isinstance(node, ast.Name):
                # Variable lookup
                return context.get(node.id)
            elif isinstance(node, ast.Attribute):
                # Dot notation - evaluate the object then get attribute
                obj = eval_node(node.value)
                if obj is None:
                    return None
                attr_name = node.attr
                if isinstance(obj, dict):
                    return obj.get(attr_name)
                else:
                    return getattr(obj, attr_name, None)
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
            result = eval_node(tree)
            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"safe_evaluate_expression_with_context: expression='{expression}' -> result={result}")
            return result
        except Exception as e:
            # Debug logging
            import logging
            logger = logging.getLogger(__name__)
            logger.debug(f"safe_evaluate_expression_with_context: expression='{expression}' failed with error: {e}")
            return False