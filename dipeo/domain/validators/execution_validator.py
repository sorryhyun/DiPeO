"""Execution Validator - Validates diagram execution flow."""

from typing import Any

from dipeo.core.base.exceptions import ValidationError
from dipeo.domain.execution.value_objects import (
    ExecutionFlow,
    FlowIssue,
    FlowIssueType,
    FlowValidationResult,
)
from dipeo.domain.validators.base_validator import BaseValidator, ValidationResult, ValidationWarning, Severity


class ExecutionValidator(BaseValidator):
    """Validates diagram execution flow using the unified framework."""
    
    def _perform_validation(self, target: Any, result: ValidationResult) -> None:
        """Perform execution flow validation."""
        if not hasattr(target, 'nodes') or not hasattr(target, 'arrows'):
            result.add_error(ValidationError("Target must be a diagram with nodes and arrows"))
            return
        
        # Use the existing flow validation logic
        flow_result = self.validate_execution_flow(target)
        
        # Convert flow validation result to unified format
        for issue in flow_result.issues:
            if issue.severity == "critical":
                result.add_error(ValidationError(
                    issue.message,
                    details={
                        "issue_type": issue.issue_type.value,
                        "node_id": issue.node_id,
                        "related_nodes": list(issue.related_nodes) if issue.related_nodes else None
                    }
                ))
            else:
                result.add_warning(ValidationWarning(
                    issue.message,
                    field_name=f"node.{issue.node_id}" if issue.node_id else None,
                    details={
                        "issue_type": issue.issue_type.value,
                        "related_nodes": list(issue.related_nodes) if issue.related_nodes else None
                    },
                    severity=Severity.WARNING
                ))
    
    def validate_execution_flow(self, diagram: Any) -> FlowValidationResult:
        """
        Validate that a diagram has a valid execution flow.
        
        Args:
            diagram: Diagram object with nodes and edges
            
        Returns:
            FlowValidationResult with validation status and issues
        """
        result = FlowValidationResult(is_valid=True, issues=[])
        
        # Extract flow structure
        nodes = {node.id: node.type for node in diagram.nodes}
        connections = {}
        for arrow in diagram.arrows:
            if arrow.source not in connections:
                connections[arrow.source] = set()
            connections[arrow.source].add(arrow.target)
        
        # Find start and endpoint nodes
        start_nodes = {
            node_id for node_id, node_type in nodes.items()
            if node_type == "start"
        }
        endpoint_nodes = {
            node_id for node_id, node_type in nodes.items()
            if node_type == "endpoint"
        }
        
        flow = ExecutionFlow(
            nodes=nodes,
            connections=connections,
            start_nodes=start_nodes,
            endpoint_nodes=endpoint_nodes
        )
        
        # Check for start node
        if not start_nodes:
            issue = FlowIssue(
                issue_type=FlowIssueType.NO_START_NODE,
                message="Diagram must have at least one start node"
            )
            result = result.add_issue(issue)
        
        # Check for endpoint node
        if not endpoint_nodes:
            issue = FlowIssue(
                issue_type=FlowIssueType.NO_ENDPOINT_NODE,
                message="Diagram should have at least one endpoint node"
            )
            result = result.add_issue(issue)
        
        # Check for circular dependencies
        cycles = flow.find_cycles()
        for cycle in cycles:
            issue = FlowIssue(
                issue_type=FlowIssueType.CIRCULAR_DEPENDENCY,
                message=f"Circular dependency detected: {' -> '.join(cycle)}",
                related_nodes=set(cycle)
            )
            result = result.add_issue(issue)
        
        # Check for unreachable nodes
        unreachable = flow.find_unreachable_nodes()
        for node_id in unreachable:
            issue = FlowIssue(
                issue_type=FlowIssueType.UNREACHABLE_NODE,
                node_id=node_id,
                message=f"Node {node_id} is not reachable from any start node"
            )
            result = result.add_issue(issue)
        
        # Validate node connections based on node types
        for node in diagram.nodes:
            node_id = node.id
            node_type = node.type
            
            # Start nodes should not have incoming connections
            if node_type == "start":
                incoming = flow.get_dependencies(node_id)
                if incoming:
                    issue = FlowIssue(
                        issue_type=FlowIssueType.INVALID_CONNECTION,
                        node_id=node_id,
                        message="Start node cannot have incoming connections",
                        related_nodes=incoming
                    )
                    result = result.add_issue(issue)
            
            # Endpoint nodes should not have outgoing connections
            elif node_type == "endpoint":
                outgoing = connections.get(node_id, set())
                if outgoing:
                    issue = FlowIssue(
                        issue_type=FlowIssueType.INVALID_CONNECTION,
                        node_id=node_id,
                        message="Endpoint node cannot have outgoing connections",
                        related_nodes=outgoing
                    )
                    result = result.add_issue(issue)
            
            # Condition nodes should have at least 2 outgoing connections
            # Note: In DiPeO, arrows connect to handles (e.g., node_3_true_output)
            # so we can't reliably validate condition node connections here
            # This validation would need handle-aware connection mapping
        
        return result