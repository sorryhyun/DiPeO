"""Factory for creating and validating typed executable nodes."""

from typing import Any

from dipeo.core.static.generated_nodes import (
    ConditionNode,
    ExecutableNode,
    PersonJobNode,
    StartNode,
    create_executable_node,
)


class NodeFactory:
    """Creates and validates strongly-typed executable nodes."""
    
    def __init__(self):
        self.validation_errors: list[str] = []
    
    def create_typed_nodes(self, domain_nodes: list[Any]) -> list[ExecutableNode]:
        """Create strongly-typed nodes with compile-time validation."""
        typed_nodes = []
        self.validation_errors.clear()
        
        for node in domain_nodes:
            try:
                # Factory creates the appropriate immutable node type
                typed_node = create_executable_node(
                    node_type=node.type,
                    node_id=node.id,
                    position=node.position,
                    label=node.data.get("label", "") if node.data else "",
                    data=node.data or {}
                )
                
                # Additional type-specific validation
                self._validate_typed_node(typed_node)
                typed_nodes.append(typed_node)
                
            except (ValueError, TypeError) as e:
                self.validation_errors.append(
                    f"Failed to create {node.type} node {node.id}: {e}"
                )
        
        return typed_nodes
    
    def _validate_typed_node(self, node: ExecutableNode) -> None:
        """Type-specific validation using actual node types."""
        if isinstance(node, PersonJobNode):
            self._validate_person_node(node)
        elif isinstance(node, ConditionNode):
            self._validate_condition_node(node)
        elif isinstance(node, StartNode):
            self._validate_start_node(node)
    
    def _validate_person_node(self, node: PersonJobNode) -> None:
        """Validate PersonJobNode specific constraints."""
        if not node.person_id:
            self.validation_errors.append(
                f"Person node {node.id} must have person_id"
            )
        if node.max_iteration < 1:
            self.validation_errors.append(
                f"Person node {node.id} max_iteration must be >= 1"
            )
    
    def _validate_condition_node(self, node: ConditionNode) -> None:
        """Validate ConditionNode specific constraints."""
        if not node.expression and node.condition_type == "expression":
            self.validation_errors.append(
                f"Condition node {node.id} with type 'expression' must have expression"
            )
    
    def _validate_start_node(self, node: StartNode) -> None:
        """Validate StartNode specific constraints."""
        if node.trigger_mode and not node.hook_event:
            self.validation_errors.append(
                f"Start node {node.id} with trigger_mode must have hook_event"
            )
    
    def get_validation_errors(self) -> list[str]:
        """Get accumulated validation errors."""
        return self.validation_errors.copy()