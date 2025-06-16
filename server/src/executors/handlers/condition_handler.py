"""
Handler for Condition nodes - boolean logic and branching
"""

from typing import Dict, Any
import time
import re
import logging

from ..schemas.condition import ConditionNodeProps, ConditionType
from ..types import ExecutionContext

logger = logging.getLogger(__name__)


async def condition_handler(
    props: ConditionNodeProps,
    context: ExecutionContext,
    inputs: Dict[str, Any]
) -> Any:
    """Handle Condition node execution"""
    
    try:
        if props.conditionType == ConditionType.DETECT_MAX_ITERATIONS:
            result = _check_preceding_nodes_max_iterations(context)
        else:
            # Default to expression evaluation
            result = _evaluate_condition(props.expression, inputs, context)
        
        # Pass through input data while storing condition result in metadata
        # If there's only one input, pass it directly; otherwise pass the full inputs dict
        if len(inputs) == 1:
            output_data = next(iter(inputs.values()))
        elif len(inputs) > 1:
            output_data = inputs
        else:
            # No inputs, just pass through empty dict
            output_data = {}
        
        return {
            "output": output_data,
            "metadata": {
                "conditionType": props.conditionType,
                "conditionResult": result,  # Store the boolean result for flow control
                "inputs": inputs,
                "evaluatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        }
    
    except Exception as e:
        # Pass through input data even on error, but set condition result to False
        if len(inputs) == 1:
            output_data = next(iter(inputs.values()))
        elif len(inputs) > 1:
            output_data = inputs
        else:
            output_data = {}
        
        logger.error(f"Failed to evaluate condition: {str(e)}")
        return {
            "output": output_data,
            "error": f"Failed to evaluate condition: {str(e)}",
            "metadata": {
                "conditionType": props.conditionType,
                "conditionResult": False,  # Default to False on error
                "inputs": inputs,
                "error": str(e)
            }
        }


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
    # Get all incoming nodes
    node_id = context.current_node_id
    incoming_arrows = context.graph.incoming.get(node_id, [])
    
    # Track if all nodes that have max iterations defined have reached them
    has_nodes_with_max_iterations = False
    all_max_iterations_reached = True
    
    # Check all directly connected source nodes
    for arrow in incoming_arrows:
        source_node_id = arrow.source
        if not source_node_id:
            continue
        
        source_node = context.graph.nodes.get(source_node_id)
        if not source_node:
            continue
        
        # Check if this node has max iterations defined
        execution_count = context.exec_cnt.get(source_node_id, 0)
        max_iterations = source_node.max_iter
        
        if max_iterations:
            has_nodes_with_max_iterations = True
            # Check if node was skipped due to max iterations
            if hasattr(context, 'skipped') and source_node_id in context.skipped and context.skipped.get(source_node_id) == "max_iterations":
                logger.debug(f"[ConditionHandler] Node {source_node_id} was skipped due to max iterations ({execution_count}/{max_iterations})")
            elif execution_count < max_iterations:
                all_max_iterations_reached = False
                logger.debug(f"[ConditionHandler] Node {source_node_id} has NOT reached max iterations yet ({execution_count}/{max_iterations})")
            else:
                logger.debug(f"[ConditionHandler] Node {source_node_id} has reached max iterations ({execution_count}/{max_iterations})")
    
    # Also check for any nodes that might be in a cycle with this condition node
    outgoing_arrows = context.graph.outgoing.get(node_id, [])
    for out_arrow in outgoing_arrows:
        target_node_id = out_arrow.target
        if not target_node_id:
            continue
        
        # Find nodes that connect to this same target (potential loop participants)
        for check_node_id, node_arrows in context.graph.outgoing.items():
            if check_node_id == node_id:
                continue  # Skip self
            
            node_connects_to_same_target = any(
                arrow.target == target_node_id for arrow in node_arrows
            )
            
            if node_connects_to_same_target:
                loop_node = context.graph.nodes.get(check_node_id)
                if not loop_node:
                    continue
                
                execution_count = context.exec_cnt.get(check_node_id, 0)
                max_iterations = loop_node.max_iter
                
                if max_iterations:
                    has_nodes_with_max_iterations = True
                    # Check if node was skipped due to max iterations
                    if hasattr(context, 'skipped') and check_node_id in context.skipped and context.skipped.get(check_node_id) == "max_iterations":
                        logger.debug(f"[ConditionHandler] Loop participant {check_node_id} was skipped due to max iterations ({execution_count}/{max_iterations})")
                    elif execution_count < max_iterations:
                        all_max_iterations_reached = False
                        logger.debug(f"[ConditionHandler] Loop participant {check_node_id} has NOT reached max iterations yet ({execution_count}/{max_iterations})")
                    else:
                        logger.debug(f"[ConditionHandler] Loop participant {check_node_id} has reached max iterations ({execution_count}/{max_iterations})")
    
    # Return true only if we found nodes with max iterations AND all of them have reached their limit
    return has_nodes_with_max_iterations and all_max_iterations_reached