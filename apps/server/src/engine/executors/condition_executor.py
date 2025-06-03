"""
Condition node executor - handles boolean logic and branching
"""

from typing import Dict, Any
import time
import re
import logging

from .base_executor import BaseExecutor, ValidationResult, ExecutorResult

logger = logging.getLogger(__name__)


class ConditionExecutor(BaseExecutor):
    """
    Condition node executor that evaluates boolean expressions or checks max iterations.
    Supports two modes:
    - expression: Evaluates a boolean expression with variables
    - max_iterations: Checks if all nodes with max iterations have reached their limit
    """
    
    async def validate(self, node: Dict[str, Any], context: 'ExecutionContext') -> ValidationResult:
        """Validate condition node configuration"""
        errors = []
        warnings = []
        
        properties = node.get("properties", {})
        condition_type = properties.get("conditionType", "expression")
        
        if condition_type == "expression":
            # Validate condition expression
            expression = properties.get("expression", "")
            if not expression:
                errors.append("Condition expression is required")
            else:
                # Basic expression validation
                if not any(op in expression for op in ["==", "!=", "<", ">", "<=", ">=", "and", "or", "true", "false"]):
                    warnings.append("Expression may not contain valid comparison operators")
        
        elif condition_type == "max_iterations":
            # No specific validation needed for max_iterations type
            pass
        else:
            errors.append(f"Invalid condition type: {condition_type}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    async def execute(self, node: Dict[str, Any], context: 'ExecutionContext') -> ExecutorResult:
        """Execute condition node and return boolean result"""
        start_time = time.time()
        
        properties = node.get("properties", {})
        condition_type = properties.get("conditionType", "expression")
        inputs = self.get_input_values(node, context)
        
        try:
            if condition_type == "max_iterations":
                result = self._check_preceding_nodes_max_iterations(node, context)
            else:
                # Default to expression evaluation
                expression = properties.get("expression", "")
                result = self._evaluate_condition(expression, inputs, context)
            
            execution_time = time.time() - start_time
            
            return ExecutorResult(
                output=result,
                metadata={
                    "conditionType": condition_type,
                    "inputs": inputs,
                    "evaluatedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "executionTime": execution_time
                },
                cost=0.0,
                execution_time=execution_time
            )
        
        except Exception as e:
            return ExecutorResult(
                output=False,
                error=f"Failed to evaluate condition: {str(e)}",
                metadata={
                    "conditionType": condition_type,
                    "inputs": inputs,
                    "error": str(e)
                },
                cost=0.0,
                execution_time=time.time() - start_time
            )
    
    def _evaluate_condition(self, expression: str, inputs: Dict[str, Any], context: 'ExecutionContext') -> bool:
        """Evaluate a condition expression"""
        # Create evaluation context with inputs and flattened node outputs
        evaluation_context = {**inputs}
        
        # Add execution counts
        evaluation_context["executionCount"] = context.node_execution_counts
        
        # Flatten node outputs to make their properties directly accessible
        for node_id, node_output in context.node_outputs.items():
            if isinstance(node_output, dict):
                # Spread object properties to make them accessible
                evaluation_context.update(node_output)
            else:
                # For primitive values, use the node ID as key
                evaluation_context[node_id] = node_output
        
        logger.info(f"[ConditionExecutor] Evaluating '{expression}' with context: {evaluation_context}")
        
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
        
        logger.info(f"[ConditionExecutor] Evaluated expression: {evaluated_expression}")
        
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
    
    def _check_preceding_nodes_max_iterations(self, node: Dict[str, Any], context: 'ExecutionContext') -> bool:
        """Check if all nodes with max iterations have reached their limit"""
        # Get all incoming nodes
        node_id = node["id"]
        incoming_arrows = context.incoming_arrows.get(node_id, [])
        
        # Track if all nodes that have max iterations defined have reached them
        has_nodes_with_max_iterations = False
        all_max_iterations_reached = True
        
        # Check all directly connected source nodes
        for arrow in incoming_arrows:
            source_node_id = arrow.get("source")
            if not source_node_id:
                continue
            
            source_node = context.nodes_by_id.get(source_node_id)
            if not source_node:
                continue
            
            # Check if this node has max iterations defined
            execution_count = context.node_execution_counts.get(source_node_id, 0)
            node_data = source_node.get("data", {})
            max_iterations = node_data.get("iterationCount") or node_data.get("maxIterations")
            
            if max_iterations:
                has_nodes_with_max_iterations = True
                if execution_count < max_iterations:
                    all_max_iterations_reached = False
                    logger.info(f"[ConditionExecutor] Node {source_node_id} has NOT reached max iterations yet ({execution_count}/{max_iterations})")
                else:
                    logger.info(f"[ConditionExecutor] Node {source_node_id} has reached max iterations ({execution_count}/{max_iterations})")
        
        # Also check for any nodes that might be in a cycle with this condition node
        outgoing_arrows = context.outgoing_arrows.get(node_id, [])
        for out_arrow in outgoing_arrows:
            target_node_id = out_arrow.get("target")
            if not target_node_id:
                continue
            
            # Find nodes that connect to this same target (potential loop participants)
            for check_node_id, node_arrows in context.outgoing_arrows.items():
                if check_node_id == node_id:
                    continue  # Skip self
                
                node_connects_to_same_target = any(
                    arrow.get("target") == target_node_id for arrow in node_arrows
                )
                
                if node_connects_to_same_target:
                    loop_node = context.nodes_by_id.get(check_node_id)
                    if not loop_node:
                        continue
                    
                    execution_count = context.node_execution_counts.get(check_node_id, 0)
                    node_data = loop_node.get("data", {})
                    max_iterations = node_data.get("iterationCount") or node_data.get("maxIterations")
                    
                    if max_iterations:
                        has_nodes_with_max_iterations = True
                        if execution_count < max_iterations:
                            all_max_iterations_reached = False
                            logger.info(f"[ConditionExecutor] Loop participant {check_node_id} has NOT reached max iterations yet ({execution_count}/{max_iterations})")
                        else:
                            logger.info(f"[ConditionExecutor] Loop participant {check_node_id} has reached max iterations ({execution_count}/{max_iterations})")
        
        # Return true only if we found nodes with max iterations AND all of them have reached their limit
        return has_nodes_with_max_iterations and all_max_iterations_reached