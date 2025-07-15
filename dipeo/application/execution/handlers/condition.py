
import logging
from typing import TYPE_CHECKING, Any, Optional

from pydantic import BaseModel

from dipeo.application.execution.handler_factory import register_handler
from dipeo.application.execution.types import TypedNodeHandler
from dipeo.application.execution.execution_request import ExecutionRequest
from dipeo.application.unified_service_registry import (
    DIAGRAM,
    CONDITION_EVALUATION_SERVICE,
    NODE_EXEC_COUNTS,
)
from dipeo.core.static.executable_diagram import ExecutableDiagram
from dipeo.core.static.generated_nodes import ConditionNode
from dipeo.core.execution.node_output import ConditionOutput, NodeOutputProtocol
from dipeo.models import ConditionNodeData, NodeExecutionStatus, NodeType

if TYPE_CHECKING:
    from dipeo.application.execution.execution_runtime import ExecutionRuntime
    from dipeo.core.dynamic.execution_context import ExecutionContext

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
    
    def validate(self, request: ExecutionRequest[ConditionNode]) -> Optional[str]:
        """Validate the execution request."""
        # Check for required services
        if not request.services.get(CONDITION_EVALUATION_SERVICE.name):
            return "Condition evaluation service not available"
        
        if not request.services.get(DIAGRAM.name):
            return "Diagram service not available"
            
        return None
    

    async def pre_execute(
        self,
        node: ConditionNode,
        execution: "ExecutionRuntime"
    ) -> dict[str, Any]:
        """Pre-execute logic for ConditionNode."""
        return {
            "condition_type": node.condition_type,
            "expression": node.expression,
            "node_indices": node.node_indices
        }
    
    async def execute_request(self, request: ExecutionRequest[ConditionNode]) -> NodeOutputProtocol:
        """Execute the condition with the unified request object."""
        # Get node and context from request
        node = request.node
        context = request.context
        inputs = request.inputs
        
        # Get services from services dict
        evaluation_service = (
            self.condition_evaluation_service or 
            request.services.get(CONDITION_EVALUATION_SERVICE.name)
        )
        diagram = request.services.get(DIAGRAM.name)
        
        if not evaluation_service or not diagram:
            raise ValueError("Required services not available")
        
        # Direct typed access to node properties
        condition_type = node.condition_type
        expression = node.expression
        node_indices = node.node_indices
        
        # Evaluate condition based on type
        if condition_type == "detect_max_iterations":
            result = self._evaluate_max_iterations_with_outputs(
                evaluation_service, diagram, context, node
            )
        elif condition_type == "check_nodes_executed":
            # New condition type using executed_nodes field
            target_nodes = node_indices or []
            # Build node_outputs dict from context
            node_outputs = {}
            for node in diagram.nodes:
                node_result = context.get_node_result(node.id)
                if node_result and 'value' in node_result:
                    # Create a simple dict with node_id and value for the service
                    node_outputs[str(node.id)] = {
                        'node_id': node.id,
                        'value': node_result['value']
                    }
            result = evaluation_service.check_nodes_executed(
                target_node_ids=target_nodes,
                node_outputs=node_outputs
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
            if condition_type == "detect_max_iterations":
                aggregated_conversations = self._aggregate_conversation_states(context, diagram)
                logger.debug(f"[CONDITION] Aggregated conversations for condtrue: {aggregated_conversations}")
                output_value = {"condtrue": aggregated_conversations if aggregated_conversations else inputs}
            else:
                output_value = {"condtrue": inputs if inputs else {}}
        else:
            # When condition is false, output goes to "false" branch only
            # For detect_max_iterations, we need to pass the conversation state back
            if condition_type == "detect_max_iterations":
                # Get the latest conversation state from the Pessimist node (or any person_job node)
                latest_conversation = None
                for node in diagram.nodes:
                    if hasattr(node, 'type') and node.type == 'person_job':
                        node_result = context.get_node_result(node.id)
                        if node_result:
                            # Handle result dict
                            value = node_result.get('value')
                            if isinstance(value, dict) and 'conversation' in value:
                                latest_conversation = {"messages": value['conversation']}
                
                # Pass conversation state if found, otherwise pass inputs
                output_value = {"condfalse": latest_conversation if latest_conversation else inputs}
            else:
                output_value = {"condfalse": inputs if inputs else {}}

        # Extract true/false outputs from the output_value
        true_output = output_value.get("condtrue") if result else None
        false_output = output_value.get("condfalse") if not result else None
        
        return ConditionOutput(
            value=result,
            node_id=node.id,
            true_output=true_output,
            false_output=false_output,
            metadata={"condition_type": condition_type}
        )
    
    
    def _extract_execution_states(self, context: "ExecutionContext", diagram: "ExecutableDiagram") -> dict[str, dict[str, Any]]:
        execution_states = {}
        
        # Get state for each node in the diagram
        for node in diagram.nodes:
            node_state = context.get_node_state(node.id)
            if node_state:
                state_dict = {
                    'status': getattr(node_state, 'status', 'pending')
                }
                if hasattr(node_state, 'status'):
                    state_dict['status'] = str(node_state.status.value) if hasattr(node_state.status, 'value') else str(node_state.status)
                execution_states[str(node.id)] = state_dict
        
        return execution_states
    
    def _aggregate_conversation_states(self, context: "ExecutionContext", diagram: Any) -> dict[str, Any]:
        """Aggregate conversation states from all person_job nodes that have executed."""
        import logging

        logger = logging.getLogger(__name__)
        
        aggregated = {"messages": []}
        
        # Find all person_job nodes that have executed (have outputs)
        person_job_nodes = []
        for node in diagram.nodes:
            if hasattr(node, 'type') and node.type == 'person_job':
                # Only include nodes that have already executed (have outputs)
                node_result = context.get_node_result(node.id)
                if node_result:
                    person_job_nodes.append(node)
        

        # Collect conversations from each person_job node's output
        for node in person_job_nodes:
            node_result = context.get_node_result(node.id)
            if not node_result:
                continue
            # Handle result dict from protocol
            value = node_result.get('value')
            if isinstance(value, dict) and 'conversation' in value:
                aggregated["messages"].extend(value['conversation'])
                logger.debug(f"Added {len(value['conversation'])} messages from node {node.id}")
        
        logger.debug(f"Aggregated {len(aggregated['messages'])} total messages from {len(person_job_nodes)} executed person_job nodes")
        return aggregated
    
    def _extract_node_exec_counts(self, context: "ExecutionContext") -> dict[str, int] | None:
        # Try to get exec counts from ExecutionContext
        if hasattr(context, '_exec_counts'):
            return context._exec_counts
        
        # NODE_EXEC_COUNTS should be passed in services dict
        # No fallback to context.get_service()
        return None
    
    def _evaluate_max_iterations_with_outputs(
        self, 
        evaluation_service: Any, 
        diagram: Any, 
        context: "ExecutionContext",
        node: ConditionNode
    ) -> bool:
        
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
            # Check if this node has been executed at least once
            exec_count = context.get_node_execution_count(node.id)
            if exec_count > 0:
                found_executed = True
                
                # Check node status for MAXITER_REACHED
                node_state = context.get_node_state(node.id)
                if node_state and hasattr(node_state, 'status'):
                    # Use the MAXITER_REACHED status
                    logger.debug(f"[CONDITION] Node {node.id} status: {node_state.status}")
                    if node_state.status != NodeExecutionStatus.MAXITER_REACHED:
                        all_reached_max = False
                        break
                else:
                    # No state found, can't be at max
                    logger.debug(f"[CONDITION] No state found for node {node.id}, falling back to exec count check")
                    all_reached_max = False
                    break

        result = found_executed and all_reached_max
        logger.debug(f"[CONDITION] detect_max_iterations result: {result} (found_executed={found_executed}, all_reached_max={all_reached_max})")
        return result