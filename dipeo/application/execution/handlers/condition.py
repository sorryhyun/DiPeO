
from typing import Any, Type

from pydantic import BaseModel

from dipeo.application.execution.context.unified_execution_context import UnifiedExecutionContext
from dipeo.application.utils import create_node_output
from dipeo.application import register_handler
from dipeo.application.execution.handler_factory import BaseNodeHandler
from dipeo.models import ConditionNodeData, NodeOutput
from dipeo.core.static.nodes import ConditionNode


@register_handler
class ConditionNodeHandler(BaseNodeHandler):
    
    def __init__(self, condition_evaluation_service=None, diagram_storage_service=None):
        self.condition_evaluation_service = condition_evaluation_service
        self.diagram_storage_service = diagram_storage_service


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
    
    def _resolve_service(self, context: UnifiedExecutionContext, services: dict[str, Any], service_name: str) -> Any | None:
        service = context.get_service(service_name)
        if not service:
            service = services.get(service_name)
        return service

    async def execute(
        self,
        props: BaseModel,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        import logging
        logger = logging.getLogger(__name__)
        
        # Extract typed node from services if available
        typed_node = services.get("typed_node")
        
        if typed_node and isinstance(typed_node, ConditionNode):
            # Convert typed node to props
            condition_props = ConditionNodeData(
                label=typed_node.label,
                condition_type=typed_node.condition_type,
                expression=typed_node.expression,
                node_indices=typed_node.node_indices
            )
        elif isinstance(props, ConditionNodeData):
            condition_props = props
        else:
            # Handle unexpected case
            return create_node_output(
                {"default": ""}, 
                {"error": "Invalid node data provided"},
                node_id=context.current_node_id,
                executed_nodes=context.executed_nodes
            )
        
        # Execute using props-based logic
        return await self._execute_with_props(condition_props, context, inputs, services)
    
    async def _execute_with_props(
        self,
        props: ConditionNodeData,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        import logging
        logger = logging.getLogger(__name__)
        
        # Resolve services
        evaluation_service = self._resolve_service(context, services, "condition_evaluation_service")
        diagram = self._resolve_service(context, services, "diagram")
        
        # Evaluate condition based on type
        if props.condition_type == "detect_max_iterations":
            logger.debug(f"Detect max iterations: has node_outputs={hasattr(context, 'node_outputs')}, executed_nodes={context.executed_nodes if hasattr(context, 'executed_nodes') else 'N/A'}")
            
            # Use new approach with NodeOutput data if available
            if hasattr(context, 'node_outputs') and context.executed_nodes:
                # New approach: Use executed_nodes and node outputs
                logger.debug("Using new approach with NodeOutput data")
                result = self._evaluate_max_iterations_with_outputs(
                    evaluation_service, diagram, context, props
                )
            else:
                # Fallback to old approach for backward compatibility
                logger.debug("Using fallback approach")
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

        # Debug logging for condition result
        logger.debug(f"Condition result: {result}, inputs: {inputs}")
        
        # Output data to the appropriate branch based on condition result
        # Only create output for the active branch to prevent execution of the inactive branch
        if result:
            # When condition is true, output goes to "true" branch only
            output_value = {"condtrue": inputs if inputs else {}}
            logger.debug("Outputting to condtrue branch")
        else:
            # When condition is false, output goes to "false" branch only
            output_value = {"condfalse": inputs if inputs else {}}
            logger.debug("Outputting to condfalse branch")
        
        return create_node_output(
            output_value, 
            {"condition_result": result},
            node_id=context.current_node_id,
            executed_nodes=context.executed_nodes
        )
    
    def _extract_execution_states(self, context: UnifiedExecutionContext) -> dict[str, dict[str, Any]]:
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
    
    def _extract_node_exec_counts(self, context: UnifiedExecutionContext) -> dict[str, int] | None:
        # Try to get exec counts from UnifiedExecutionContext
        if hasattr(context, '_exec_counts'):
            return context._exec_counts
        
        # Fallback: try to get from service (for backward compatibility)
        exec_info_service = context.get_service('node_exec_counts')
        if exec_info_service:
            return exec_info_service
        return None
    
    def _evaluate_max_iterations_with_outputs(
        self, 
        evaluation_service: Any, 
        diagram: Any, 
        context: UnifiedExecutionContext,
        props: ConditionNodeData
    ) -> bool:
        from dipeo.models import NodeType
        import logging
        logger = logging.getLogger(__name__)
        
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
                
                # Debug logging
                logger.debug(f"Condition check for {node.id}: exec_count={exec_count}, max_iter={max_iter}")
                
                if exec_count < max_iter:
                    all_reached_max = False
                    break
        
        # Debug logging for final result
        logger.debug(f"Max iterations evaluation: found_executed={found_executed}, all_reached_max={all_reached_max}")
        
        # Return true only if we found at least one executed person_job 
        # AND all executed ones have reached max iterations
        return found_executed and all_reached_max