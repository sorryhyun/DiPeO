"""Node readiness checking logic extracted from ExecutionRuntime."""

from typing import TYPE_CHECKING

from dipeo.core.execution.node_output import ConditionOutput
from dipeo.diagram_generated.generated_nodes import ConditionNode
from dipeo.diagram_generated.generated_nodes import PersonJobNode
from dipeo.diagram_generated.generated_nodes import StartNode
from dipeo.diagram_generated import NodeExecutionStatus, NodeID
from dipeo.application.utils.template import TemplateProcessor
import logging

if TYPE_CHECKING:
    from dipeo.core.execution.execution_tracker import ExecutionTracker
    from dipeo.domain.diagram.models.executable_diagram import ExecutableDiagram, ExecutableNode

logger = logging.getLogger(__name__)


class NodeReadinessChecker:
    """Encapsulates node readiness checking logic."""
    
    def __init__(self, diagram: "ExecutableDiagram", tracker: "ExecutionTracker"):
        self.diagram = diagram
        self.tracker = tracker
        self._template_processor = TemplateProcessor()
    
    def is_node_ready(
        self, 
        node: "ExecutableNode", 
        node_states: dict[NodeID, any]
    ) -> bool:
        # Not pending? Not ready
        state = node_states.get(node.id)
        if not state or state.status != NodeExecutionStatus.PENDING:
            return False
        
        # Start nodes are always ready when pending
        if isinstance(node, StartNode):
            return True
        
        # Check dependencies
        incoming_edges = self._get_relevant_edges(node)
        
        # All dependencies must be completed
        for edge in incoming_edges:
            if not self._is_dependency_satisfied(edge, node_states):
                return False
            
            # For condition nodes, check branch activation
            source_node = self.diagram.get_node(edge.source_node_id)
            if isinstance(source_node, ConditionNode):
                if not self._is_condition_branch_active(source_node.id, edge.source_output):
                    return False
        
        # Check template variable dependencies
        if not self._has_required_template_inputs(node, incoming_edges, node_states):
            return False
        
        return True
    
    def _get_relevant_edges(self, node: "ExecutableNode") -> list:
        """Get relevant incoming edges for a node."""
        incoming_edges = self.diagram.get_incoming_edges(node.id)
        
        # Special handling for PersonJobNodes
        if isinstance(node, PersonJobNode):
            exec_count = self.tracker.get_execution_count(node.id)

            # First execution? Check appropriate edges
            if exec_count == 0:
                # If there are ANY incoming edges targeting "first" inputs, 
                # the node MUST wait for them before executing
                first_edges = [e for e in incoming_edges if e.target_input in ("first", "HandleLabel.FIRST")]
                if first_edges:
                    return first_edges
                
                # No 'first' edges - check all non-loop edges
                # This ensures nodes wait for their regular inputs on first execution
                non_loop_edges = []
                for edge in incoming_edges:
                    source_node = self.diagram.get_node(edge.source_node_id)
                    if source_node and not isinstance(source_node, ConditionNode):
                        non_loop_edges.append(edge)
                
                # Return all edges that need to be checked (could be empty list)
                result = non_loop_edges if non_loop_edges else incoming_edges
                return result
        
        return incoming_edges
    
    def _is_dependency_satisfied(self, edge: any, node_states: dict) -> bool:
        """Check if a dependency edge is satisfied."""
        dep_state = node_states.get(edge.source_node_id)
        if not dep_state:
            return False
        
        dep_exec_count = self.tracker.get_execution_count(edge.source_node_id)
        dep_node = self.diagram.get_node(edge.source_node_id)
        
        # For PersonJobNodes that are PENDING but have executed, consider them satisfied
        if (isinstance(dep_node, PersonJobNode) and 
            dep_state.status == NodeExecutionStatus.PENDING and 
            dep_exec_count > 0):
            return True
        
        # Accept both COMPLETED and MAXITER_REACHED as valid completion states
        return dep_state.status in (
            NodeExecutionStatus.COMPLETED, 
            NodeExecutionStatus.MAXITER_REACHED
        )
    
    def _is_condition_branch_active(self, condition_node_id: NodeID, branch: str) -> bool:
        """Check if a specific branch of a condition node is active."""
        tracker_output = self.tracker.get_last_output(condition_node_id)
        if not tracker_output:
            return False
        
        if isinstance(tracker_output, ConditionOutput):
            active_branch, _ = tracker_output.get_branch_output()
            return branch == active_branch
        elif hasattr(tracker_output, 'value') and isinstance(tracker_output.value, bool):
            return (branch == "condtrue" and tracker_output.value) or \
                   (branch == "condfalse" and not tracker_output.value)
        
        return False
    
    def _extract_template_variables(self, node: "ExecutableNode") -> set[str]:
        """Extract template variables from node prompts."""
        if not isinstance(node, PersonJobNode):
            return set()
        
        variables = set()
        
        # Extract from default prompt
        if node.default_prompt:
            variables.update(self._template_processor.extract_variables(node.default_prompt))
        
        # Extract from first_only_prompt
        if node.first_only_prompt:
            variables.update(self._template_processor.extract_variables(node.first_only_prompt))
        
        return variables
    
    def _has_required_template_inputs(
        self, 
        node: "ExecutableNode", 
        edges: list,
        node_states: dict
    ) -> bool:
        """Check if all template variable dependencies are satisfied."""
        # Extract template variables from the node
        template_vars = self._extract_template_variables(node)
        if not template_vars:
            return True  # No template variables, no dependencies

        # For PersonJobNode on first execution with template variables,
        # we need to ensure all inputs providing those variables are ready
        if isinstance(node, PersonJobNode):
            exec_count = self.tracker.get_execution_count(node.id)
            logger.debug(f"Node {node.id} execution count: {exec_count}")
            
            # First execution and has template variables?
            if exec_count == 0 and template_vars:
                for edge in edges:
                    # Check if this edge's source is ready
                    if not self._is_dependency_satisfied(edge, node_states):
                        return False
        
        return True