from __future__ import annotations

from typing import Any, Dict

from ..schemas.condition import ConditionNodeProps
from ..types import RuntimeExecutionContext
from ..decorators import node
from ..utils import BaseNodeHandler, safe_eval


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
        services: Dict[str, Any]
    ) -> bool:
        """Evaluate the conditional expression.
        
        Returns:
            True if the expression evaluates to true, False otherwise
        """
        # Use the safe_eval utility we extracted earlier
        return safe_eval(props.expression, inputs, context)
    
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