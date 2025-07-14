
from typing import Any, TYPE_CHECKING
import logging

from pydantic import BaseModel

from dipeo.application.execution.context.unified_execution_context import UnifiedExecutionContext
from dipeo.application import register_handler
from dipeo.application.execution.types import TypedNodeHandler
from dipeo.models import ConditionNodeData, NodeOutput, NodeType
from dipeo.core.static.generated_nodes import ConditionNode

if TYPE_CHECKING:
    from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution

logger = logging.getLogger(__name__)


@register_handler
class ConditionNodeHandler(TypedNodeHandler[ConditionNode]):
    
    def __init__(self, condition_evaluation_service=None, diagram_storage_service=None):
        self.condition_evaluation_service = condition_evaluation_service
        self.diagram_storage_service = diagram_storage_service


    @property
    def node_class(self) -> type[ConditionNode]:
        return ConditionNode
    
    @property
    def node_type(self) -> str:
        return NodeType.condition.value

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

    async def pre_execute(
        self,
        node: ConditionNode,
        execution: "TypedStatefulExecution"
    ) -> dict[str, Any]:
        """Pre-execute logic for ConditionNode."""
        return {
            "condition_type": node.condition_type,
            "expression": node.expression,
            "node_indices": node.node_indices
        }
    
    async def execute(
        self,
        node: ConditionNode,
        context: UnifiedExecutionContext,
        inputs: dict[str, Any],
        services: dict[str, Any],
    ) -> NodeOutput:
        # Resolve services
        evaluation_service = self._resolve_service(context, services, "condition_evaluation_service")
        diagram = self._resolve_service(context, services, "diagram")
        
        # Direct typed access to node properties
        condition_type = node.condition_type
        expression = node.expression
        node_indices = node.node_indices
        
        # Evaluate condition based on type
        if condition_type == "detect_max_iterations":
            logger.debug(f"Detect max iterations: has node_outputs={hasattr(context, 'node_outputs')}, executed_nodes={context.executed_nodes if hasattr(context, 'executed_nodes') else 'N/A'}")
            
            # Use new approach with NodeOutput data if available
            if hasattr(context, 'node_outputs') and context.executed_nodes:
                # New approach: Use executed_nodes and node outputs
                result = self._evaluate_max_iterations_with_outputs(
                    evaluation_service, diagram, context, node
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
        elif condition_type == "check_nodes_executed":
            # New condition type using executed_nodes field
            target_nodes = node_indices or []
            result = evaluation_service.check_nodes_executed(
                target_node_ids=target_nodes,
                node_outputs=context.node_outputs if hasattr(context, 'node_outputs') else {}
            )
        elif condition_type == "custom":
            result = evaluation_service.evaluate_custom_expression(
                expression=expression or "",
                context_values=inputs,
            )
        else:
            # Default to false for unknown condition types
            result = False

        # Only create output for the active branch to prevent execution of the inactive branch
        if result:
            # When condition is true, output goes to "true" branch only
            # For detect_max_iterations, aggregate conversation states from all person_job nodes
            if condition_type == "detect_max_iterations" and hasattr(context, 'node_outputs'):
                aggregated_conversations = self._aggregate_conversation_states(context, diagram)
                logger.debug(f"[CONDITION] Aggregated conversations for condtrue: {aggregated_conversations}")
                output_value = {"condtrue": aggregated_conversations if aggregated_conversations else inputs}
            else:
                output_value = {"condtrue": inputs if inputs else {}}
        else:
            # When condition is false, output goes to "false" branch only
            # For detect_max_iterations, we need to pass the conversation state back
            if condition_type == "detect_max_iterations" and hasattr(context, 'node_outputs'):
                # Get the latest conversation state from the Pessimist node (or any person_job node)
                latest_conversation = None
                for node in diagram.nodes:
                    if hasattr(node, 'type') and node.type == 'person_job':
                        node_id = str(node.id)
                        if node_id in context.node_outputs:
                            output = context.node_outputs[node_id]
                            # Handle NodeOutput object
                            if isinstance(output, NodeOutput):
                                value = output.value
                                if isinstance(value, dict) and 'conversation' in value:
                                    latest_conversation = {"messages": value['conversation']}
                            # Handle dict format (backward compatibility)
                            elif isinstance(output, dict) and 'value' in output:
                                value = output['value']
                                if isinstance(value, dict) and 'conversation' in value:
                                    latest_conversation = {"messages": value['conversation']}
                
                # Pass conversation state if found, otherwise pass inputs
                output_value = {"condfalse": latest_conversation if latest_conversation else inputs}
            else:
                output_value = {"condfalse": inputs if inputs else {}}

        return self._build_output(
            output_value, 
            context,
            {"condition_result": result}
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
    
    def _aggregate_conversation_states(self, context: UnifiedExecutionContext, diagram: Any) -> dict[str, Any]:
        """Aggregate conversation states from all person_job nodes that have executed."""
        import logging
        from dipeo.models import NodeOutput
        logger = logging.getLogger(__name__)
        
        aggregated = {"messages": []}
        
        # Find all person_job nodes that have executed (have outputs)
        person_job_nodes = []
        for node in diagram.nodes:
            if hasattr(node, 'type') and node.type == 'person_job':
                node_id = str(node.id)
                # Only include nodes that have already executed (have outputs)
                if node_id in context.node_outputs:
                    person_job_nodes.append(node)
        

        # Collect conversations from each person_job node's output
        for node in person_job_nodes:
            node_id = str(node.id)
            output = context.node_outputs[node_id]
            # Handle NodeOutput object
            if isinstance(output, NodeOutput):
                value = output.value
                if isinstance(value, dict) and 'conversation' in value:
                    aggregated["messages"].extend(value['conversation'])
                    logger.debug(f"Added {len(value['conversation'])} messages from node {node_id}")
            # Handle dict format (backward compatibility)
            elif isinstance(output, dict) and 'value' in output:
                value = output['value']
                if isinstance(value, dict) and 'conversation' in value:
                    aggregated["messages"].extend(value['conversation'])
        
        logger.debug(f"Aggregated {len(aggregated['messages'])} total messages from {len(person_job_nodes)} executed person_job nodes")
        return aggregated
    
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
        node: ConditionNode
    ) -> bool:
        
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
                
                # Handle typed nodes from ExecutableDiagram
                if hasattr(node, 'max_iteration'):
                    # Direct property access for typed nodes
                    max_iter = node.max_iteration
                else:
                    # Fallback for dict-based nodes
                    max_iter = int(node.data.get("max_iteration", 1)) if hasattr(node, 'data') else 1
                
                # Debug logging
                logger.debug(f"[CONDITION] Node {node.id} exec_count={exec_count}, max_iter={max_iter}")
                if exec_count <= max_iter:
                    all_reached_max = False
                    break

        result = found_executed and all_reached_max
        logger.debug(f"[CONDITION] detect_max_iterations result: {result} (found_executed={found_executed}, all_reached_max={all_reached_max})")
        return result