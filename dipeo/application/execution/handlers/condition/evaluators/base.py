"""Base evaluator protocol for condition evaluation."""

from abc import ABC, abstractmethod
from typing import Any, Protocol, TypedDict

from dipeo.application.execution.handlers.utils import get_node_result
from dipeo.diagram_generated.unified_nodes.condition_node import ConditionNode
from dipeo.domain.execution.context.execution_context import ExecutionContext


class EvaluationResult(TypedDict):
    result: bool
    metadata: dict[str, Any]
    output_data: dict[str, Any] | None


class ConditionEvaluator(Protocol):
    async def evaluate(
        self, node: ConditionNode, context: ExecutionContext, inputs: dict[str, Any]
    ) -> EvaluationResult: ...


class BaseConditionEvaluator(ABC):
    def extract_node_outputs(self, context: ExecutionContext) -> dict[str, Any]:
        node_outputs = {}
        all_nodes = context.diagram.get_nodes_by_type(None) or context.diagram.nodes
        for node in all_nodes:
            node_result = get_node_result(context, node.id)
            if node_result and "value" in node_result:
                node_outputs[str(node.id)] = {"node_id": node.id, "value": node_result["value"]}
        return node_outputs

    @abstractmethod
    async def evaluate(
        self, node: ConditionNode, context: ExecutionContext, inputs: dict[str, Any]
    ) -> EvaluationResult:
        pass
