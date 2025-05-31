"""Simplified Condition node executor."""

from typing import Any, Dict, Tuple, Optional

from .base_executor import BaseExecutor
from ..core.execution_context import ExecutionContext
from ..core.skip_manager import SkipManager


class ConditionExecutor(BaseExecutor):
    """Executor for Condition nodes - handles boolean branching logic."""
    
    def __init__(self):
        """Initialize the condition executor."""
        super().__init__()
    
    async def execute(
        self,
        node: Dict[str, Any],
        context: ExecutionContext,
        skip_manager: SkipManager,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute a Condition node.
        
        Evaluates a condition and returns True or False to determine
        which branch of execution to follow.
        
        Args:
            node: The node configuration
            context: The execution context
            skip_manager: The skip manager (not used here)
            **kwargs: Additional arguments
            
        Returns:
            Tuple of (boolean_result, 0.0) - conditions have no cost
        """
        # Prepare inputs
        inputs = self._prepare_inputs(node, context)
        
        # Get the condition configuration
        condition_type = self._get_node_property(node, 'data.conditionType', 'simple')
        
        if condition_type == 'simple':
            result = await self._evaluate_simple_condition(inputs, context)
        elif condition_type == 'expression':
            result = await self._evaluate_expression(inputs, context)
        else:
            # Default to False for unknown condition types
            result = False
        
        # Conditions have no cost
        return result, 0.0
    
    async def _evaluate_simple_condition(
        self,
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> bool:
        """Evaluate a simple condition (equality, comparison, etc).
        
        Args:
            inputs: The resolved input values
            context: The execution context
            
        Returns:
            Boolean result of the condition
        """
        left_value = inputs.get('leftValue', '')
        right_value = inputs.get('rightValue', '')
        operator = inputs.get('operator', '==')
        
        # Convert to appropriate types
        left_value = self._convert_value(left_value)
        right_value = self._convert_value(right_value)
        
        # Evaluate based on operator
        if operator == '==':
            return left_value == right_value
        elif operator == '!=':
            return left_value != right_value
        elif operator == '>':
            return self._safe_compare(left_value, right_value, lambda a, b: a > b)
        elif operator == '<':
            return self._safe_compare(left_value, right_value, lambda a, b: a < b)
        elif operator == '>=':
            return self._safe_compare(left_value, right_value, lambda a, b: a >= b)
        elif operator == '<=':
            return self._safe_compare(left_value, right_value, lambda a, b: a <= b)
        elif operator == 'contains':
            return str(right_value) in str(left_value)
        elif operator == 'not_contains':
            return str(right_value) not in str(left_value)
        else:
            return False
    
    async def _evaluate_expression(
        self,
        inputs: Dict[str, Any],
        context: ExecutionContext
    ) -> bool:
        """Evaluate a Python expression.
        
        Args:
            inputs: The resolved input values
            context: The execution context
            
        Returns:
            Boolean result of the expression
        """
        expression = inputs.get('expression', 'False')
        
        # Create a safe evaluation context
        eval_context = {
            'outputs': context.node_outputs,
            'True': True,
            'False': False,
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool
        }
        
        try:
            # Evaluate the expression in a restricted context
            result = eval(expression, {"__builtins__": {}}, eval_context)
            return bool(result)
        except Exception:
            # Return False if expression evaluation fails
            return False
    
    def _convert_value(self, value: Any) -> Any:
        """Convert string values to appropriate types.
        
        Args:
            value: The value to convert
            
        Returns:
            The converted value
        """
        if not isinstance(value, str):
            return value
        
        # Try to convert to number
        try:
            # Try int first
            if '.' not in value:
                return int(value)
            else:
                return float(value)
        except ValueError:
            pass
        
        # Check for boolean
        if value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        
        # Return as string
        return value
    
    def _safe_compare(self, left: Any, right: Any, comparison_func) -> bool:
        """Safely compare two values.
        
        Args:
            left: Left operand
            right: Right operand
            comparison_func: Function to perform the comparison
            
        Returns:
            Result of comparison or False if types incompatible
        """
        try:
            return comparison_func(left, right)
        except TypeError:
            # Try string comparison if numeric comparison fails
            return comparison_func(str(left), str(right))
    
    async def validate_inputs(
        self,
        node: Dict[str, Any],
        context: ExecutionContext
    ) -> Optional[str]:
        """Validate Condition node inputs.
        
        Args:
            node: The node configuration
            context: The execution context
            
        Returns:
            Error message if validation fails, None if valid
        """
        condition_type = self._get_node_property(node, 'data.conditionType', 'simple')
        
        if condition_type == 'simple':
            if not self._get_node_property(node, 'data.operator'):
                return "Simple condition requires an operator"
        elif condition_type == 'expression':
            if not self._get_node_property(node, 'data.expression'):
                return "Expression condition requires an expression"
        
        return None