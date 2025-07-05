"""Condition node handler - handles conditional logic in diagram execution."""

import ast
import operator
from typing import Any

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
from dipeo_core.execution import create_node_output
from dipeo_domain.models import ConditionNodeData, NodeOutput
from pydantic import BaseModel

from ..utils.template import substitute_template


@register_handler
class ConditionNodeHandler(BaseNodeHandler):
    """Handler for condition nodes."""

    @property
    def node_type(self) -> str:
        return "condition"

    @property
    def schema(self) -> type[BaseModel]:
        return ConditionNodeData

    @property
    def description(self) -> str:
        return "Condition node: supports detect_max_iterations and custom expressions"

    async def execute(
        self,
        props: ConditionNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute condition node."""
        
        if props.condition_type == "detect_max_iterations":
            result = await self._evaluate_max_iterations(context, services)
        elif props.condition_type == "custom":
            result = await self._evaluate_custom_expression(props.expression or "", inputs)
        else:
            # Default to false for unknown condition types
            result = False

        # Output data to the appropriate branch based on condition result
        # The execution engine expects outputs keyed by branch name
        # We need to pass through all inputs, including conversation data
        if result:
            # When condition is true, output goes to "true" branch
            # Pass through all inputs as a single value
            output_value = {"condtrue": inputs if inputs else {}, "condfalse": None}
        else:
            # When condition is false, output goes to "false" branch
            # Pass through all inputs as a single value
            output_value = {"condfalse": inputs if inputs else {}, "condtrue": None}
        
        return create_node_output(output_value, {"condition_result": result})

    async def _evaluate_max_iterations(self, context: RuntimeContext, services: dict[str, Any]) -> bool:
        """Evaluate if all upstream person_job nodes reached their max_iterations."""
        # Get diagram to check upstream nodes
        diagram = services.get("diagram")
        if not diagram:
            return False

        # Check if ALL upstream person_job nodes have reached their max_iterations
        found_person_job = False
        all_reached_max = True
        
        for edge in context.edges:
            if edge.get("target", "").startswith(context.current_node_id):
                src_node_id = edge.get("source", "").split("_")[0]
                src_node = next((n for n in diagram.nodes if n.id == src_node_id), None)
                if src_node and src_node.type == "person_job":
                    found_person_job = True
                    exec_count = context.get_node_execution_count(src_node_id)
                    max_iter = int((src_node.data or {}).get("max_iteration", 1))
                    if exec_count < max_iter:
                        all_reached_max = False
                        break
        
        # Return true only if we found at least one person_job AND all have reached max
        return found_person_job and all_reached_max

    async def _evaluate_custom_expression(self, expression: str, inputs: dict[str, Any]) -> bool:
        """Evaluate a custom expression with variable substitution."""
        if not expression:
            return False
        
        try:
            # Substitute variables in the expression
            substituted_expr, missing_keys, _ = substitute_template(expression, inputs)
            
            # If there are missing keys, the condition fails
            if missing_keys:
                return False
            
            # Safe evaluation of the expression
            # This is a simple implementation that supports basic comparisons
            # For more complex expressions, consider using a proper expression parser
            result = self._safe_eval(substituted_expr)
            
            return bool(result)
        except Exception:
            # If evaluation fails, return False
            return False

    def _safe_eval(self, expression: str) -> Any:
        """Safely evaluate a boolean expression."""
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
