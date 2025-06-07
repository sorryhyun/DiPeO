"""
Condition node executor - handles boolean logic and branching
"""

from typing import Dict, Any, TYPE_CHECKING
import time
import re
import logging

from .base_executor import BaseExecutor, ExecutorResult
from .utils import get_input_values
from .validator import ValidationResult, validate_required_fields, validate_enum_field

if TYPE_CHECKING:
    from ..types import Ctx

logger = logging.getLogger(__name__)


class ConditionExecutor(BaseExecutor):
    """
    Condition node executor that evaluates boolean expressions or checks max iterations.
    Supports two modes:
    - expression: Evaluates a boolean expression with variables
    - max_iterations: Checks if all nodes with max iterations have reached their limit
    """
    
    async def validate(self, node: Dict[str, Any], context: 'Ctx') -> ValidationResult:
        """Validate condition node configuration"""
        errors = []
        warnings = []
        
        properties = node.get("properties", {})
        condition_type = properties.get("conditionType", "expression")
        
        # Validate condition type enum
        enum_error = validate_enum_field(
            properties, 
            "conditionType", 
            ["expression", "detect_max_iterations"],
            case_sensitive=True
        )
        if enum_error:
            errors.append(enum_error)
        
        if condition_type == "expression":
            # Validate required expression field
            field_errors = validate_required_fields(
                properties,
                ["expression"],
                {"expression": "Condition expression"}
            )
            errors.extend(field_errors)
            
            # Basic expression validation
            expression = properties.get("expression", "")
            if expression and not any(op in expression for op in ["==", "!=", "<", ">", "<=", ">=", "and", "or", "true", "false"]):
                warnings.append("Expression may not contain valid comparison operators")
        
        elif condition_type == "detect_max_iterations":
            # No specific validation needed for max_iterations type
            pass
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def execute(self, node: Dict[str, Any], context: 'Ctx') -> ExecutorResult:
        """Execute condition node and return boolean result"""
        start_time = time.time()
        
        properties = node.get("properties", {})
        condition_type = properties.get("conditionType", "expression")
        inputs = get_input_values(node, context)
        
        try:
            if condition_type in ["detect_max_iterations"]:
                result = self._check_preceding_nodes_max_iterations(node, context)
            else:
                # Default to expression evaluation
                expression = properties.get("expression", "")
                result = self._evaluate_condition(expression, inputs, context)
            
            execution_time = time.time() - start_time
            
            # Pass through input data while storing condition result in metadata
            # If there's only one input, pass it directly; otherwise pass the full inputs dict
            if len(inputs) == 1:
                output_data = next(iter(inputs.values()))
            elif len(inputs) > 1:
                output_data = inputs
            else:
                # No inputs, just pass through empty dict
                output_data = {}
            
            return ExecutorResult(
                output=output_data,
                metadata={
                    "conditionType": condition_type,
                    "conditionResult": result,  # Store the boolean result for flow control
                    "inputs": inputs,
                    "evaluatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "executionTime": execution_time
                },
                execution_time=execution_time
            )
        
        except Exception as e:
            # Pass through input data even on error, but set condition result to False
            if len(inputs) == 1:
                output_data = next(iter(inputs.values()))
            elif len(inputs) > 1:
                output_data = inputs
            else:
                output_data = {}
            
            return ExecutorResult(
                output=output_data,
                error=f"Failed to evaluate condition: {str(e)}",
                metadata={
                    "conditionType": condition_type,
                    "conditionResult": False,  # Default to False on error
                    "inputs": inputs,
                    "error": str(e)
                },
                execution_time=time.time() - start_time
            )
    
    def _evaluate_condition(self, expression: str, inputs: Dict[str, Any], context: 'Ctx') -> bool:
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
        
        logger.debug(f"[ConditionExecutor] Evaluating '{expression}' with context: {evaluation_context}")
        
        # Simple expression evaluation
        return self._evaluate_expression(expression, evaluation_context)
    
    def _evaluate_expression(self, expression: str, context: Dict[str, Any]) -> bool:
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
        
        logger.debug(f"[ConditionExecutor] Evaluated expression: {evaluated_expression}")
        
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
    
    def _check_preceding_nodes_max_iterations(self, node: Dict[str, Any], context: 'Ctx') -> bool:
        """Check if all nodes with max iterations have reached their limit"""
        # Get all incoming nodes
        node_id = node["id"]
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
                if source_node_id in context.skipped and context.skipped.get(source_node_id) == "max_iterations":
                    logger.debug(f"[ConditionExecutor] Node {source_node_id} was skipped due to max iterations ({execution_count}/{max_iterations})")
                elif execution_count < max_iterations:
                    all_max_iterations_reached = False
                    logger.debug(f"[ConditionExecutor] Node {source_node_id} has NOT reached max iterations yet ({execution_count}/{max_iterations})")
                else:
                    logger.debug(f"[ConditionExecutor] Node {source_node_id} has reached max iterations ({execution_count}/{max_iterations})")
        
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
                        if check_node_id in context.skipped and context.skipped.get(check_node_id) == "max_iterations":
                            logger.debug(f"[ConditionExecutor] Loop participant {check_node_id} was skipped due to max iterations ({execution_count}/{max_iterations})")
                        elif execution_count < max_iterations:
                            all_max_iterations_reached = False
                            logger.debug(f"[ConditionExecutor] Loop participant {check_node_id} has NOT reached max iterations yet ({execution_count}/{max_iterations})")
                        else:
                            logger.debug(f"[ConditionExecutor] Loop participant {check_node_id} has reached max iterations ({execution_count}/{max_iterations})")
        
        # Return true only if we found nodes with max iterations AND all of them have reached their limit
        return has_nodes_with_max_iterations and all_max_iterations_reached