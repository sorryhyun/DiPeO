from __future__ import annotations

import re
from typing import Any, Dict

from ..schemas.condition import ConditionNodeProps
from ..types import RuntimeExecutionContext
from ..decorators import node
from ..utils import BaseNodeHandler


@node(
    node_type="condition",
    schema=ConditionNodeProps,
    description="Evaluate conditional expressions for branching logic"
)
class ConditionHandler(BaseNodeHandler):
    """Conditional branching node using BaseNodeHandler.
    
    This refactored version is much simpler - it only needs to
    implement the core evaluation logic. All error handling,
    timing, and metadata building is handled by the base class.
    
    The original handler was ~50 lines, this one is ~20 lines.
    """
    
    async def _execute_core(
        self,
        props: ConditionNodeProps,
        context: RuntimeExecutionContext,
        inputs: Dict[str, Any],
        services: Dict[str, Any]  # noqa: ARG002
    ) -> bool:
        """Evaluate the conditional expression.
        
        Returns:
            True if the expression evaluates to true, False otherwise
        """
        # Handle optional expression
        if not props.expression:
            return False
            
        # For now, implement expression evaluation directly here
        # since safe_eval expects a different ExecutionContext type
        namespace: Dict[str, Any] = {"executionCount": context.exec_cnt, **inputs}
        
        # Flatten previous node outputs for easy access
        for node_id, output in context.outputs.items():
            if isinstance(output, dict):
                namespace.update(output)
            else:
                namespace[node_id] = output
        
        expr = props.expression
        # Replace {{var}} placeholders
        var_pattern = re.compile(r"\{\{(\w+)\}\}")
        
        def replace_var(match: re.Match[str]) -> str:
            val = namespace.get(match.group(1))
            if val is None:
                return "None"
            elif isinstance(val, str):
                return f'"{val}"'
            return str(val)
        
        expr = var_pattern.sub(replace_var, expr)
        
        # Replace bare identifiers with their literal value
        for key, val in namespace.items():
            formatted_val = f'"{val}"' if isinstance(val, str) else str(val) if val is not None else "None"
            expr = re.sub(rf"\b{re.escape(key)}\b", formatted_val, expr)
        
        # Normalize JS-style logical operators to Python
        expr = (
            expr.replace("&&", " and ")
            .replace("||", " or ")
            .replace("===", "==")
            .replace("!==", "!=")
        )
        
        try:
            return bool(eval(expr, {"__builtins__": {}}, {}))  # nosec B307
        except Exception:
            return False
    
    def _build_metadata(
        self,
        start_time: float,
        props: ConditionNodeProps,
        context: RuntimeExecutionContext,
        result: Any
    ) -> Dict[str, Any]:
        """Add condition-specific metadata."""
        metadata = super()._build_metadata(start_time, props, context, result)
        metadata.update({
            "expression": props.expression,
            "result": result,
        })
        return metadata