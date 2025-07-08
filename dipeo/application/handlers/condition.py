"""Condition node handler - handles conditional logic in diagram execution."""

from typing import Any

from pydantic import BaseModel

from dipeo.domain.services.ports.execution_context import ExecutionContextPort
from dipeo.application.utils import create_node_output
from dipeo.application import BaseNodeHandler, register_handler
from dipeo.models import ConditionNodeData, NodeOutput


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
        return ["condition_evaluation_service", "diagram"]

    @property
    def description(self) -> str:
        return "Condition node: supports detect_max_iterations and custom expressions"
    
    def _resolve_service(self, context: ExecutionContextPort, services: dict[str, Any], service_name: str) -> Any | None:
        """Helper to resolve service from context or services dict."""
        service = context.get_service(service_name)
        if not service:
            service = services.get(service_name)
        return service

    async def execute(
        self,
        props: ConditionNodeData,
        context: ExecutionContextPort,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        """Execute condition node by delegating to domain service."""
        # Resolve services
        evaluation_service = self._resolve_service(context, services, "condition_evaluation_service")
        diagram = self._resolve_service(context, services, "diagram")
        
        # Evaluate condition based on type
        if props.condition_type == "detect_max_iterations":
            # Use new approach with NodeOutput data if available
            if hasattr(context, 'node_outputs') and context.executed_nodes:
                # New approach: Use executed_nodes and node outputs
                result = self._evaluate_max_iterations_with_outputs(
                    evaluation_service, diagram, context, props
                )
            else:
                # Fallback to old approach for backward compatibility
                execution_states = self._extract_execution_states(context)
                node_exec_counts = self._extract_node_exec_counts(context)
                
                result = evaluation_service.evaluate_max_iterations(
                    diagram=diagram,
                    execution_states=execution_states,
                    node_exec_counts=node_exec_counts,
                )
        elif props.condition_type == "check_nodes_executed":
            # New condition type using executed_nodes field
            target_nodes = props.node_indices or []
            result = evaluation_service.check_nodes_executed(
                target_node_ids=target_nodes,
                node_outputs=context.node_outputs if hasattr(context, 'node_outputs') else {}
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
        
        return create_node_output(
            output_value, 
            {"condition_result": result},
            node_id=context.current_node_id,
            executed_nodes=context.executed_nodes
        )
    
    def _extract_execution_states(self, context: ExecutionContextPort) -> dict[str, dict[str, Any]]:
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
    
    def _extract_node_exec_counts(self, context: ExecutionContextPort) -> dict[str, int] | None:
        """Extract node execution counts from context."""
        exec_info_service = context.get_service('node_exec_counts')
        if exec_info_service:
            return exec_info_service
        return None
    
    def _evaluate_max_iterations_with_outputs(
        self, 
        evaluation_service: Any, 
        diagram: Any, 
        context: ExecutionContextPort,
        props: ConditionNodeData
    ) -> bool:
        """Evaluate max iterations using the new NodeOutput data.
        
        This improved approach uses the executed_nodes field from NodeOutput
        to track execution state more efficiently.
        """
        from dipeo.models import NodeType
        
        # Get executed nodes list
        executed_nodes = set(context.executed_nodes) if context.executed_nodes else set()
        
        # Find all person_job nodes
        person_job_nodes = [
            node for node in diagram.nodes 
            if node.type == NodeType.person_job.value
        ]
        
        if not person_job_nodes:
            return False
        
        # Check if all executed person_job nodes have reached max iterations
        all_reached_max = True
        found_executed = False
        
        for node in person_job_nodes:
            # Check if this node has been executed
            if node.id in executed_nodes:
                found_executed = True
                exec_count = context.get_node_execution_count(node.id)
                max_iter = int(node.data.get("max_iteration", 1))
                
                if exec_count < max_iter:
                    all_reached_max = False
                    break
        
        # Return true only if we found at least one executed person_job 
        # AND all executed ones have reached max iterations
        return found_executed and all_reached_max