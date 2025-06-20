"""
Handler for Condition nodes - boolean logic and branching
"""

from typing import Dict, Any
import time
import re
import logging

from ..schemas.condition import ConditionNodeProps, ConditionType
from ..types import ExecutionContext
from src.__generated__.models import NodeOutput
from ..decorators import node

logger = logging.getLogger(__name__)


@node(
    node_type="condition",
    schema=ConditionNodeProps,
    description="Conditional branching based on expression evaluation"
)
async def condition_handler(
    props: ConditionNodeProps,
    context: ExecutionContext,
    inputs: Dict[str, Any],
    services: Dict[str, Any]
) -> Any:
    """Handle Condition node execution"""
    
    try:
        if props.conditionType == ConditionType.DETECT_MAX_ITERATIONS:
            result = _check_preceding_nodes_max_iterations(context)
        else:
            # Default to expression evaluation
            result = _evaluate_condition(props.expression, inputs, context)
        
        # Return unified NodeOutput format
        return NodeOutput(
            value=result,  # The boolean result is the main value
            metadata={
                "conditionType": props.conditionType.value if props.conditionType else None,
                "expression": props.expression,
                "evaluatedExpression": props.expression,  # For compatibility
                "evaluatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        )
    
    except Exception as e:
        logger.error(f"Failed to evaluate condition: {str(e)}")
        # Return NodeOutput with error
        return NodeOutput(
            value=False,  # Default to False on error
            metadata={
                "conditionType": props.conditionType.value if props.conditionType else None,
                "expression": props.expression,
                "evaluatedExpression": props.expression,
                "error": str(e),
                "evaluatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        )


def _evaluate_condition(expression: str, inputs: Dict[str, Any], context: ExecutionContext) -> bool:
    """Evaluate a condition expression"""
    # Create evaluation context with inputs and flattened node outputs
    evaluation_context = {**inputs}
    
    # Add execution counts
    evaluation_context["executionCount"] = context.exec_cnt
    
    # Flatten node outputs to make their properties directly accessible
    for node_id, node_output in context.outputs.items():
        if isinstance(node_output, dict):
            # Spread object properties to make them accessible
            evaluation_context.update(node_output)
        else:
            # For primitive values, use the node ID as key
            evaluation_context[node_id] = node_output
    
    logger.debug(f"[ConditionHandler] Evaluating '{expression}' with context: {evaluation_context}")
    
    # Simple expression evaluation
    return _evaluate_expression(expression, evaluation_context)


def _evaluate_expression(expression: str, context: Dict[str, Any]) -> bool:
    """Simple expression evaluator for conditions"""
    # Replace variables in the expression
    evaluated_expression = expression
    
    # Replace variable references with their values
    for key, value in context.items():
        # Use word boundaries to avoid partial matches
        pattern = rf'\b{re.escape(key)}\b'
        if isinstance(value, str):
            replacement = f'"{value}"'
        else:
            replacement = str(value)
        evaluated_expression = re.sub(pattern, replacement, evaluated_expression)
    
    # Also handle {{variable}} syntax
    def replace_template(match):
        var_name = match.group(1)
        value = context.get(var_name)
        if value is None:
            return "None"
        elif isinstance(value, str):
            return f'"{value}"'
        else:
            return str(value)
    
    evaluated_expression = re.sub(r'\{\{(\w+)\}\}', replace_template, evaluated_expression)
    
    logger.debug(f"[ConditionHandler] Evaluated expression: {evaluated_expression}")
    
    try:
        # Convert to Python boolean operators
        evaluated_expression = evaluated_expression.replace(" and ", " and ")
        evaluated_expression = evaluated_expression.replace(" or ", " or ")
        evaluated_expression = evaluated_expression.replace("&&", " and ")
        evaluated_expression = evaluated_expression.replace("||", " or ")
        evaluated_expression = evaluated_expression.replace("===", "==")
        evaluated_expression = evaluated_expression.replace("!==", "!=")
        
        # Use eval with restricted context for safety
        # In production, use a proper expression parser like simpleeval
        result = eval(evaluated_expression, {"__builtins__": {}}, {})
        return bool(result)
    except Exception as e:
        logger.warning(f"Failed to evaluate expression '{expression}': {e}")
        return False


def _check_preceding_nodes_max_iterations(context: ExecutionContext) -> bool:
    """Check if all nodes with max iterations have reached their limit"""
    # In the new architecture, we don't have graph information
    # This feature requires additional context that should be passed
    # For now, return False to maintain backward compatibility
    logger.warning("[ConditionHandler] DETECT_MAX_ITERATIONS is not fully supported in the new architecture")
    return False