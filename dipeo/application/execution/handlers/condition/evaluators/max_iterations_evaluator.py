"""Evaluator for max iterations condition."""

import logging
from typing import Any

from dipeo.application.execution.handlers.utils import get_node_execution_count
from dipeo.config.base_logger import get_module_logger
from dipeo.diagram_generated.unified_nodes.condition_node import ConditionNode, NodeType
from dipeo.domain.execution.execution_context import ExecutionContext

from .base import BaseConditionEvaluator, EvaluationResult

logger = get_module_logger(__name__)


class MaxIterationsEvaluator(BaseConditionEvaluator):
    """Evaluates whether all person_job nodes have reached max iterations."""

    async def evaluate(
        self, node: ConditionNode, context: ExecutionContext, inputs: dict[str, Any]
    ) -> EvaluationResult:
        person_job_nodes = context.diagram.get_nodes_by_type(NodeType.PERSON_JOB)

        if not person_job_nodes:
            return EvaluationResult(
                result=False, metadata={"reason": "No person_job nodes found"}, output_data=None
            )

        all_reached_max = True
        found_executed = False

        for node in person_job_nodes:
            exec_count = get_node_execution_count(context, node.id)

            if exec_count > 0:
                found_executed = True

                node_state = context.state.get_node_state(node.id)

                # Use >= because if exec_count equals max_iteration, we've done all iterations
                if exec_count < node.max_iteration:
                    logger.debug(
                        f"MaxIterationsEvaluator: node {node.id} NOT reached max: {exec_count} < {node.max_iteration}"
                    )
                    all_reached_max = False
                    break
                else:
                    logger.debug(
                        f"MaxIterationsEvaluator: node {node.id} REACHED max: {exec_count} >= {node.max_iteration}"
                    )

        result = found_executed and all_reached_max
        output_data = inputs

        logger.debug(
            f"MaxIterationsEvaluator: found_executed={found_executed}, "
            f"all_reached_max={all_reached_max}, result={result}"
        )

        if (
            hasattr(node, "expose_index_as")
            and node.expose_index_as
            and hasattr(context, "get_variable")
        ):
            loop_value = context.get_variable(node.expose_index_as)
            if loop_value is not None:
                if isinstance(output_data, dict):
                    output_data[node.expose_index_as] = loop_value
                else:
                    output_data = {"data": output_data, node.expose_index_as: loop_value}

        return EvaluationResult(
            result=result,
            metadata={
                "found_executed": found_executed,
                "all_reached_max": all_reached_max,
                "person_job_count": len(person_job_nodes),
            },
            output_data=output_data,
        )
