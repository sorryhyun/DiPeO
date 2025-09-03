"""Factory for creating and validating typed executable nodes."""

from typing import Any

from dipeo.diagram_generated import NodeType
from dipeo.diagram_generated.generated_nodes import (
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
                
                # Set join policy at compile time based on node type and properties
                # Condition nodes always use "any" policy
                if typed_node.type == NodeType.CONDITION:
                    # Use object.__setattr__ to set attribute on frozen dataclass
                    # This is a hack but necessary since we're adding runtime attributes
                    object.__setattr__(typed_node, 'join_policy', "any")
                
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
        if not node.person:
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
        from dipeo.diagram_generated import HookTriggerMode
        
        if node.trigger_mode == HookTriggerMode.HOOK and not node.hook_event:
            self.validation_errors.append(
                f"Start node {node.id} with trigger_mode 'hook' must have hook_event"
            )
    
    def get_validation_errors(self) -> list[str]:
        """Get accumulated validation errors."""
        return self.validation_errors.copy()