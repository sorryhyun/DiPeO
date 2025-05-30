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
            return self._evaluate_max_iterations(state, kwargs.get('diagram', {})), 0.0
        
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
            resolved_inputs = resolve_inputs(incoming_arrows, state.context)
            
            # Create evaluation context
            eval_context = {
                **vars_map,
                **resolved_inputs,
                'inputs': inputs if inputs else resolved_inputs
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
    
    def _evaluate_max_iterations(self, state: ExecutionState, diagram: dict) -> bool:
        """Evaluate if all executed PersonJob nodes have reached their max iterations.
        
        Args:
            state: Current execution state with counts
            diagram: Full diagram data containing node configurations
            
        Returns:
            True if all executed PersonJob nodes reached their max iterations
        """
        nodes = diagram.get('nodes', [])
        personjob_nodes = [
            n for n in nodes 
            if n.get('data', {}).get('type') == 'person_job'
        ]
        
        if not personjob_nodes:
            logger.warning("no_personjob_nodes_for_max_iterations")
            return True
        
        # Check each PersonJob node that has been executed
        all_at_max = True
        executed_count = 0
        
        for node in personjob_nodes:
            node_id = node['id']
            iteration_count = node.get('data', {}).get('iterationCount', 1)
            current_count = state.counts.get(node_id, 0)
            
            # Only consider nodes that have been executed at least once
            if current_count > 0:
                executed_count += 1
                if current_count < iteration_count:
                    all_at_max = False
                    logger.debug(
                        "personjob_not_at_max",
                        node_id=node_id,
                        current=current_count,
                        max=iteration_count
                    )
        
        # If no PersonJob nodes have been executed yet, return False
        if executed_count == 0:
            return False
        
        logger.info(
            "max_iterations_check",
            all_at_max=all_at_max,
            executed_nodes=executed_count
        )
        
        return all_at_max