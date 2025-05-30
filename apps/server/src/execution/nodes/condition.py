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

    def _evaluate_max_iterations(self, state: ExecutionState, diagram: dict) -> bool:
        """
        Evaluate if all executed PersonJob nodes have been skipped due to max iterations.
        Note: Despite the name, this checks for completion/skipping, not just iteration count.
        """
        nodes = diagram.get('nodes', [])
        personjob_nodes = [
            n for n in nodes
            if n.get('data', {}).get('type') == 'person_job' or
               n.get('type') in ['personjobNode', 'personJobNode']
        ]

        if not personjob_nodes:
            logger.warning("no_personjob_nodes_for_max_iterations")
            return True

        # Check if all executed PersonJob nodes were skipped
        all_complete = True
        any_executed = False

        for node in personjob_nodes:
            node_id = node['id']

            # Check if node was executed
            if state.counts.get(node_id, 0) > 0:
                any_executed = True

                # Check the NODE's context, not global context!
                node_context = state.context.get(node_id)

                # The skipped node's context is {"skipped_max_iter": True}
                is_skipped = (isinstance(node_context, dict) and
                              node_context.get('skipped_max_iter') == True)

                if not is_skipped:
                    all_complete = False
                    logger.debug(
                        "personjob_not_skipped",
                        node_id=node_id,
                        node_context=node_context,
                        execution_count=state.counts.get(node_id, 0)
                    )

        # Only return true if some were executed AND all of those are complete
        result = any_executed and all_complete

        logger.info(
            "max_iterations_detected",  # Better logging name
            all_complete=all_complete,
            any_executed=any_executed,
            result=result
        )

        return result