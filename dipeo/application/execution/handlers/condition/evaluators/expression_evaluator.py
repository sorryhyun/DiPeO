import ast
import operator
from typing import Any

from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)


class ConditionEvaluator:
    @staticmethod
    def _get_allowed_operators() -> dict[type, Any]:
        return {
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

    @staticmethod
    def _get_allowed_functions() -> dict[str, Any]:
        return {
            "len": len,
            "abs": abs,
            "min": min,
            "max": max,
            "sum": sum,
            "all": all,
            "any": any,
            "bool": bool,
            "int": int,
            "float": float,
            "str": str,
            "list": list,
            "dict": dict,
            "tuple": tuple,
            "set": set,
            "round": round,
        }

    def check_nodes_executed(
        self,
        target_node_ids: list[str],
        node_outputs: dict[str, Any],
    ) -> bool:
        if not target_node_ids or not node_outputs:
            return False

        all_executed = set()
        for output in node_outputs.values():
            if hasattr(output, "executed_nodes") and output.executed_nodes:
                all_executed.update(output.executed_nodes)

        return all(node_id in all_executed for node_id in target_node_ids)

    def evaluate_custom_expression(
        self,
        expression: str,
        context_values: dict[str, Any],
    ) -> bool:
        if not expression:
            return False

        return self.safe_evaluate_expression_with_context(expression, context_values)

    def _safe_eval_expression(
        self, expression: str, context: dict[str, Any] | None = None, log_result: bool = False
    ) -> Any:
        allowed_operators = self._get_allowed_operators()
        allowed_functions = self._get_allowed_functions()

        try:
            tree = ast.parse(expression, mode="eval")
        except SyntaxError:
            return False

        def eval_node(node):
            if isinstance(node, ast.Expression):
                return eval_node(node.body)
            elif isinstance(node, ast.Constant):
                return node.value
            elif isinstance(node, ast.Str):
                return node.s
            elif isinstance(node, ast.Num):
                return node.n
            elif isinstance(node, ast.Name):
                if context is not None:
                    return context.get(node.id)
                raise ValueError("Variable access requires context")
            elif isinstance(node, ast.Attribute):
                if context is None:
                    raise ValueError("Attribute access requires context")
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
                else:
                    return any(values)
            elif isinstance(node, ast.UnaryOp):
                op_func = allowed_operators.get(type(node.op))
                if op_func is None:
                    raise ValueError(f"Unsupported operator: {type(node.op).__name__}")
                return op_func(eval_node(node.operand))
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    func_name = node.func.id
                    if func_name not in allowed_functions:
                        raise ValueError(f"Function '{func_name}' is not allowed")
                    func = allowed_functions[func_name]
                    args = [eval_node(arg) for arg in node.args]
                    if node.keywords:
                        raise ValueError("Keyword arguments are not supported")
                    return func(*args)
                else:
                    raise ValueError("Only simple function calls are supported")
            else:
                raise ValueError(f"Unsupported node type: {type(node).__name__}")

        try:
            result = eval_node(tree)
            if log_result:
                logger.debug(f"Expression '{expression}' evaluated to: {result}")
            return result
        except Exception as e:
            if log_result:
                logger.debug(f"Expression '{expression}' failed with error: {e}")
            return False

    def safe_evaluate_expression(self, expression: str) -> Any:
        return self._safe_eval_expression(expression, context=None, log_result=False)

    def safe_evaluate_expression_with_context(
        self, expression: str, context: dict[str, Any]
    ) -> Any:
        return self._safe_eval_expression(expression, context=context, log_result=True)
