"""Condition evaluation logic."""

from typing import Any, Dict, Optional, Union
import json
import logging
import operator
from functools import reduce

log = logging.getLogger(__name__)


class ConditionEvaluator:
    """Evaluates conditions for conditional nodes."""
    
    OPERATORS = {
        'eq': operator.eq,
        'ne': operator.ne,
        'gt': operator.gt,
        'gte': operator.ge,
        'lt': operator.lt,
        'lte': operator.le,
        'in': lambda x, y: x in y,
        'not_in': lambda x, y: x not in y,
        'contains': lambda x, y: y in x,
        'not_contains': lambda x, y: y not in x,
        'startswith': lambda x, y: str(x).startswith(str(y)),
        'endswith': lambda x, y: str(x).endswith(str(y)),
        'and': lambda *args: all(args),
        'or': lambda *args: any(args),
        'not': operator.not_,
    }
    
    @classmethod
    def evaluate_condition(
        cls,
        condition: Union[str, Dict[str, Any]],
        context: Dict[str, Any]
    ) -> bool:
        """Evaluate a condition against a context.
        
        Args:
            condition: The condition to evaluate (string expression or dict)
            context: The context containing values for evaluation
            
        Returns:
            Boolean result of the condition
        """
        try:
            if isinstance(condition, str):
                return cls._evaluate_string_condition(condition, context)
            elif isinstance(condition, dict):
                return cls._evaluate_dict_condition(condition, context)
            else:
                # Simple truthy evaluation
                return bool(condition)
        except Exception as e:
            log.error(f"Error evaluating condition: {e}")
            return False
    
    @classmethod
    def _evaluate_string_condition(cls, condition: str, context: Dict[str, Any]) -> bool:
        """Evaluate a string-based condition."""
        try:
            # Simple expression evaluation
            # WARNING: This is for demonstration. In production, use a safe expression parser
            # First try direct boolean values
            if condition.lower() == 'true':
                return True
            elif condition.lower() == 'false':
                return False
            
            # Try to evaluate as a simple comparison
            # Format: "key operator value"
            parts = condition.split()
            if len(parts) == 3:
                key, op, value = parts
                actual_value = cls._get_nested_value(context, key)
                
                # Try to parse value
                try:
                    value = json.loads(value)
                except:
                    pass  # Keep as string
                
                # Map common operators
                op_map = {
                    '==': 'eq',
                    '!=': 'ne',
                    '>': 'gt',
                    '>=': 'gte',
                    '<': 'lt',
                    '<=': 'lte',
                }
                op = op_map.get(op, op)
                
                if op in cls.OPERATORS:
                    return cls.OPERATORS[op](actual_value, value)
            
            # Fall back to checking if the value exists and is truthy
            return bool(cls._get_nested_value(context, condition))
            
        except Exception as e:
            log.error(f"Error in string condition evaluation: {e}")
            return False
    
    @classmethod
    def _evaluate_dict_condition(cls, condition: Dict[str, Any], context: Dict[str, Any]) -> bool:
        """Evaluate a dictionary-based condition."""
        # Handle logical operators
        if 'and' in condition:
            conditions = condition['and']
            return all(cls.evaluate_condition(c, context) for c in conditions)
        
        if 'or' in condition:
            conditions = condition['or']
            return any(cls.evaluate_condition(c, context) for c in conditions)
        
        if 'not' in condition:
            return not cls.evaluate_condition(condition['not'], context)
        
        # Handle comparison operators
        if 'field' in condition and 'operator' in condition:
            field = condition['field']
            op = condition['operator']
            value = condition.get('value')
            
            actual_value = cls._get_nested_value(context, field)
            
            if op in cls.OPERATORS:
                if op in ['and', 'or', 'not']:
                    # These are handled above
                    return False
                return cls.OPERATORS[op](actual_value, value)
        
        # Handle direct field checks
        for key, expected_value in condition.items():
            actual_value = cls._get_nested_value(context, key)
            if actual_value != expected_value:
                return False
        
        return True
    
    @staticmethod
    def _get_nested_value(data: Dict[str, Any], path: str) -> Any:
        """Get a value from nested dictionary using dot notation."""
        keys = path.split('.')
        try:
            return reduce(lambda d, key: d[key], keys, data)
        except (KeyError, TypeError):
            return None
    
    @classmethod
    def validate_condition(cls, condition: Union[str, Dict[str, Any]]) -> Optional[str]:
        """Validate that a condition is well-formed.
        
        Returns:
            Error message if invalid, None if valid
        """
        try:
            if isinstance(condition, str):
                # Basic validation for string conditions
                if not condition.strip():
                    return "Empty condition"
            elif isinstance(condition, dict):
                # Validate dict conditions
                if not condition:
                    return "Empty condition dictionary"
                
                # Check for valid operators
                valid_keys = {'and', 'or', 'not', 'field', 'operator', 'value'}
                if 'field' in condition:
                    if 'operator' not in condition:
                        return "Missing operator for field condition"
                    if condition['operator'] not in cls.OPERATORS:
                        return f"Invalid operator: {condition['operator']}"
                elif not any(key in condition for key in ['and', 'or', 'not']):
                    # Direct field comparison - this is ok
                    pass
            else:
                return f"Invalid condition type: {type(condition)}"
            
            return None
        except Exception as e:
            return f"Validation error: {str(e)}"