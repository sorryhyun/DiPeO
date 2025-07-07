"""Condition node handler - handles conditional logic in diagram execution."""

from typing import Any, Optional

from dipeo.core import BaseNodeHandler, register_handler
from dipeo.application import UnifiedExecutionContext
from dipeo.application.utils import create_node_output
from dipeo.models import ConditionNodeData, NodeOutput
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
    def requires_services(self) -> list[str]:
        return ["condition_evaluation", "diagram"]

    @property
    def description(self) -> str:
        return "Condition node: supports detect_max_iterations and custom expressions"
    
    def _resolve_service(self, context: UnifiedExecutionContext, services: dict[str, Any], service_name: str) -> Optional[Any]:
        """Helper to resolve service from context or services dict."""
        service = context.get_service(service_name)
        if not service:
            service = services.get(service_name)
        return service

    async def execute(
        self,
        props: ConditionNodeData,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute condition node by delegating to domain service."""
        # Resolve services
        evaluation_service = self._resolve_service(context, services, "condition_evaluation")
        diagram = self._resolve_service(context, services, "diagram")
        
        # Evaluate condition based on type
        if props.condition_type == "detect_max_iterations":
            # Prepare execution states and counts for domain service
            execution_states = self._extract_execution_states(context)
            node_exec_counts = self._extract_node_exec_counts(context)
            
            result = evaluation_service.evaluate_max_iterations(
                diagram=diagram,
                execution_states=execution_states,
                node_exec_counts=node_exec_counts,
            )
        elif props.condition_type == "custom":
            result = evaluation_service.evaluate_custom_expression(
                expression=props.expression or "",
                context_values=inputs,
            )
        else:
            # Default to false for unknown condition types
            result = False

        # Output data to the appropriate branch based on condition result
        # Only create output for the active branch to prevent execution of the inactive branch
        if result:
            # When condition is true, output goes to "true" branch only
            output_value = {"condtrue": inputs if inputs else {}}
        else:
            # When condition is false, output goes to "false" branch only
            output_value = {"condfalse": inputs if inputs else {}}
        
        return create_node_output(output_value, {"condition_result": result})
    
    def _extract_execution_states(self, context: UnifiedExecutionContext) -> dict[str, dict[str, Any]]:
        """Extract execution states from context."""
        execution_states = {}
        
        if hasattr(context.execution_state, 'node_states'):
            for node_id, node_state in context.execution_state.node_states.items():
                state_dict = {
                    'status': getattr(node_state, 'status', 'pending')
                }
                if hasattr(node_state, 'status'):
                    state_dict['status'] = str(node_state.status.value) if hasattr(node_state.status, 'value') else str(node_state.status)
                execution_states[node_id] = state_dict
        
        return execution_states
    
    def _extract_node_exec_counts(self, context: UnifiedExecutionContext) -> Optional[dict[str, int]]:
        """Extract node execution counts from context."""
        exec_info_service = context.get_service('node_exec_counts')
        if exec_info_service:
            return exec_info_service
        return None