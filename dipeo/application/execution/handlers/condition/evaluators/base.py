"""Base evaluator protocol for condition evaluation."""

from abc import ABC, abstractmethod
from typing import Any, Protocol, TypedDict

from dipeo.core.execution.execution_context import ExecutionContext
from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram
from dipeo.diagram_generated.generated_nodes import ConditionNode


class EvaluationResult(TypedDict):
    """Result of condition evaluation."""
    result: bool
    metadata: dict[str, Any]
    output_data: dict[str, Any] | None


class ConditionEvaluator(Protocol):
    """Protocol for condition-specific evaluators."""
    
    async def evaluate(
        self,
        node: ConditionNode,
        context: ExecutionContext,
        diagram: ExecutableDiagram,
        inputs: dict[str, Any]
    ) -> EvaluationResult:
        """Evaluate the condition.
        
        Args:
            node: The condition node
            context: Execution context
            diagram: The executable diagram
            inputs: Input data
            
        Returns:
            Evaluation result with metadata
        """
        ...


class BaseConditionEvaluator(ABC):
    """Base class for condition evaluators with common functionality."""
    
    def extract_node_outputs(self, context: ExecutionContext, diagram: ExecutableDiagram) -> dict[str, Any]:
        """Extract node outputs from execution context."""
        node_outputs = {}
        for node in diagram.nodes:
            node_result = context.get_node_result(node.id)
            if node_result and 'value' in node_result:
                node_outputs[str(node.id)] = {
                    'node_id': node.id,
                    'value': node_result['value']
                }
        return node_outputs
    
    @abstractmethod
    async def evaluate(
        self,
        node: ConditionNode,
        context: ExecutionContext,
        diagram: ExecutableDiagram,
        inputs: dict[str, Any]
    ) -> EvaluationResult:
        """Evaluate the condition."""
        pass