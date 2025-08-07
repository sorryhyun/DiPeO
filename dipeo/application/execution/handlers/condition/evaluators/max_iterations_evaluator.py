"""Evaluator for max iterations condition."""

import logging
from typing import Any

from dipeo.core.execution.execution_context import ExecutionContext
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.diagram_generated.generated_nodes import ConditionNode, NodeType
from dipeo.diagram_generated.enums import Status

from .base import BaseConditionEvaluator, EvaluationResult
from ..conversation_aggregator import ConversationAggregator

logger = logging.getLogger(__name__)


class MaxIterationsEvaluator(BaseConditionEvaluator):
    """Evaluates whether all person_job nodes have reached max iterations."""
    
    def __init__(self):
        self._aggregator = ConversationAggregator()
    
    async def evaluate(
        self,
        node: ConditionNode,
        context: ExecutionContext,
        diagram: ExecutableDiagram,
        inputs: dict[str, Any]
    ) -> EvaluationResult:
        """Check if all executed person_job nodes have reached max iterations."""
        # Find all person_job nodes
        person_job_nodes = [
            n for n in diagram.nodes 
            if n.type == NodeType.PERSON_JOB.value
        ]
        
        if not person_job_nodes:
            return EvaluationResult(
                result=False,
                metadata={"reason": "No person_job nodes found"},
                output_data=None
            )
        
        # Check if all executed person_job nodes have reached max iterations
        all_reached_max = True
        found_executed = False
        
        for node in person_job_nodes:
            # Check if this node has been executed at least once
            exec_count = context.get_node_execution_count(node.id)
            if exec_count > 0:
                found_executed = True
                
                # Check node status for MAXITER_REACHED
                node_state = context.get_node_state(node.id)
                if node_state and hasattr(node_state, 'status'):
                    if node_state.status != Status.MAXITER_REACHED:
                        all_reached_max = False
                        break
                else:
                    # No state found, can't be at max
                    all_reached_max = False
                    break
        
        result = found_executed and all_reached_max
        
        # Prepare output data based on result
        if result:
            # Aggregate all conversation states when max iterations reached
            aggregated = self._aggregator.aggregate_conversations(context, diagram)
            output_data = {"condtrue": aggregated if aggregated else inputs}
        else:
            # Get latest conversation state for false branch
            latest_conversation = self._aggregator.get_latest_conversation(context, diagram)
            output_data = {"condfalse": latest_conversation if latest_conversation else inputs}
        
        # Log evaluation details
        logger.debug(
            f"MaxIterationsEvaluator: found_executed={found_executed}, "
            f"all_reached_max={all_reached_max}, result={result}"
        )
        
        return EvaluationResult(
            result=result,
            metadata={
                "found_executed": found_executed,
                "all_reached_max": all_reached_max,
                "person_job_count": len(person_job_nodes)
            },
            output_data=output_data
        )