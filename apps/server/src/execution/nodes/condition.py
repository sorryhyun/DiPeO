"""Condition node executor for branching logic."""

import re
import structlog
from typing import Any, Dict, List, Tuple

from .base import BaseNodeExecutor
from ..state import ExecutionState
from ...utils.resolve_utils import resolve_inputs

logger = structlog.get_logger(__name__)


class ConditionNodeExecutor(BaseNodeExecutor):
    """Executes Condition nodes for branching logic.
    
    Condition nodes evaluate boolean expressions to determine
    which path the execution should take.
    """
    
    async def execute(
        self, 
        node: dict, 
        vars_map: Dict[str, Any], 
        inputs: List[Any],
        state: ExecutionState,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute a Condition node.
        
        Args:
            node: Node configuration with condition expression
            vars_map: Variable mappings for condition evaluation
            inputs: Input values from incoming arrows
            state: Current execution state
            **kwargs: Must include 'incoming_arrows'
            
        Returns:
            Tuple of (boolean_result, 0.0)
        """
        node_id = self.get_node_id(node)
        data = self.get_node_data(node)
        incoming_arrows = kwargs.get('incoming_arrows', [])
        
        # Check for max_iterations condition type
        condition_type = data.get("conditionType", "").strip()
        if condition_type == "max_iterations":
            return self._evaluate_max_iterations(state, incoming_arrows), 0.0
        
        # Get the condition expression
        condition_expr = data.get("condition", "").strip()
        if not condition_expr:
            logger.warning(
                "empty_condition",
                node_id=node_id
            )
            return False, 0.0
        
        try:
            # Resolve inputs from incoming arrows
            vars_map_resolved, inputs_resolved = resolve_inputs(
                node_id, incoming_arrows, state.context
            )
            
            # Create evaluation context
            eval_context = {
                **vars_map,
                **vars_map_resolved,
                'inputs': inputs if inputs else inputs_resolved,
                # Add common convenience variables
                'input': inputs[0] if inputs else (inputs_resolved[0] if inputs_resolved else ''),
                'output': inputs[0] if inputs else (inputs_resolved[0] if inputs_resolved else '')
            }
            
            # Evaluate the condition
            result = self._evaluate_condition(condition_expr, eval_context)
            
            # Cache the result in state
            state.condition_values[node_id] = result
            
            logger.info(
                "condition_evaluated",
                node_id=node_id,
                condition=condition_expr,
                result=result
            )
            
            return result, 0.0
            
        except Exception as e:
            logger.error(
                "condition_evaluation_failed",
                node_id=node_id,
                condition=condition_expr,
                error=str(e),
                available_vars=list(eval_context.keys()) if 'eval_context' in locals() else [],
                exc_info=True
            )
            # Default to False on error
            return False, 0.0
    
    def _evaluate_condition(self, condition: str, context: Dict[str, Any]) -> bool:
        """Safely evaluate a condition expression.
        
        Args:
            condition: Python expression to evaluate
            context: Variables available for evaluation
            
        Returns:
            Boolean result of evaluation
        """
        # Remove potentially dangerous constructs
        if any(danger in condition for danger in ['import', '__', 'exec', 'eval']):
            raise ValueError(f"Unsafe condition expression: {condition}")
        
        try:
            # Evaluate in restricted context
            result = eval(condition, {"__builtins__": {}}, context)
            return bool(result)
        except Exception as e:
            logger.debug(
                "condition_eval_error",
                condition=condition,
                error=str(e)
            )
            raise

    def _evaluate_max_iterations(self, state: ExecutionState, incoming_arrows: List[dict]) -> bool:
        """
        Simplified: Just check if all upstream nodes are skipped.
        """
        if not incoming_arrows:
            return True
        
        # Get all source node IDs from incoming arrows
        incoming_nodes = []
        for arrow in incoming_arrows:
            source = arrow.get('source')
            if source:
                incoming_nodes.append(source)
        
        if not incoming_nodes:
            return True
        
        # Check if all incoming nodes are skipped
        result = all(
            state.context.get(node_id, {}).get('skipped', False) 
            for node_id in incoming_nodes
        )
        
        logger.info(
            "max_iterations_evaluated",
            incoming_nodes=incoming_nodes,
            result=result
        )
        
        return result