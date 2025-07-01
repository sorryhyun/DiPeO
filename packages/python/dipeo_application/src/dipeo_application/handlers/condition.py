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
        if props.condition_type != "detect_max_iterations":
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

        # Forward all inputs to outputs, preserving conversation state
        value: dict[str, Any] = {}

        # Copy all inputs to outputs
        if inputs:
            value.update(inputs)

            # For person_job nodes, conversation state comes as "conversation" key
            # We need to ensure it's available in both the output and branch-specific keys
            if "conversation" in inputs and "default" in inputs:
                # This is typical person_job output format
                # Keep both default (text) and conversation (history)
                pass  # Already copied via update()
            elif "default" not in value and inputs:
                # Ensure we have a default output
                if "conversation" in inputs:
                    value["default"] = inputs["conversation"]
                else:
                    first_key = next(iter(inputs.keys()), None)
                    if first_key:
                        value["default"] = inputs[first_key]

        # Return output based on result
        if result:
            # Max iterations reached - output on True branch
            return create_node_output({"True": value.get("default", "")}, {"condition_result": result})
        else:
            # Iterations remaining - output on False branch 
            return create_node_output({"False": value.get("default", "")}, {"condition_result": result})
