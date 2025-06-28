"""Condition node handler - handles conditional logic in diagram execution."""

from typing import Any

from dipeo_core import BaseNodeHandler, RuntimeContext, register_handler
from dipeo_core.execution import create_node_output
from dipeo_domain.models import ConditionNodeData, NodeOutput
from pydantic import BaseModel


@register_handler
class ConditionNodeHandler(BaseNodeHandler):
    """Handler for condition nodes."""

    @property
    def node_type(self) -> str:
        return "condition"

    @property
    def schema(self) -> type[BaseModel]:
        return ConditionNodeData

    @property
    def description(self) -> str:
        return "Condition node: currently supports detect_max_iterations"

    async def execute(
        self,
        props: ConditionNodeData,
        context: RuntimeContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute condition node."""
        if props.conditionType != "detect_max_iterations":
            return create_node_output({"False": None}, {"condition_result": False})

        # Get diagram to check upstream nodes
        diagram = services.get("diagram")
        if not diagram:
            return create_node_output({"False": None}, {"condition_result": False})

        # True only if all upstream person_job nodes reached their max_iterations
        result = True
        for edge in context.edges:
            if edge.get("target", "").startswith(context.current_node_id):
                src_node_id = edge.get("source", "").split(":")[0]
                src_node = next((n for n in diagram.nodes if n.id == src_node_id), None)
                if src_node and src_node.type == "person_job":
                    exec_count = context.get_node_execution_count(src_node_id)
                    max_iter = int((src_node.data or {}).get("maxIteration", 1))
                    if exec_count < max_iter:
                        result = False
                        break

        # Forward inputs directly
        value: dict[str, Any] = {**inputs}

        if "default" not in value and inputs:
            if "conversation" in inputs:
                value["default"] = inputs["conversation"]
            else:
                first_key = next(iter(inputs.keys()), None)
                if first_key:
                    value["default"] = inputs[first_key]

        return create_node_output(value, {"condition_result": result})
