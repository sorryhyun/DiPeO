"""Protocol for runtime input resolution with transformation support."""

from abc import abstractmethod
from typing import Any, Protocol, Callable

from dipeo.domain.diagram.models.executable_diagram import ExecutableEdgeV2, ExecutableNode
from dipeo.core.execution.execution_context import ExecutionContext
from dipeo.core.execution.node_output import NodeOutputProtocol


class TransformationRule(Protocol):
    """Protocol for data transformation rules."""
    
    @abstractmethod
    def apply(self, value: Any, source_type: str, target_type: str) -> Any:
        """Apply transformation to a value."""
        ...
    
    @abstractmethod
    def can_transform(self, source_type: str, target_type: str) -> bool:
        """Check if this rule can transform between types."""
        ...


class RuntimeResolver(Protocol):
    """Resolves node inputs at runtime with transformation support.
    
    This protocol handles runtime input resolution including:
    - Value extraction from node outputs
    - Type transformations
    - Default value handling
    - Conditional input resolution
    """
    
    @abstractmethod
    def resolve_node_inputs(
        self,
        node: ExecutableNode,
        edges: list[ExecutableEdgeV2],
        context: ExecutionContext
    ) -> dict[str, Any]:
        """
        Resolve all inputs for a node at runtime.
        
        Args:
            node: The node to resolve inputs for
            edges: All edges in the diagram
            context: Current execution context with node states
            
        Returns:
            Dictionary of resolved input values by handle name
        """
        ...
    
    @abstractmethod
    def resolve_single_input(
        self,
        node: ExecutableNode,
        input_name: str,
        edge: ExecutableEdgeV2,
        context: ExecutionContext
    ) -> Any:
        """
        Resolve a single input value through an edge.
        
        Args:
            node: Target node
            input_name: Name of the input to resolve
            edge: The edge providing the input
            context: Current execution context
            
        Returns:
            Resolved and transformed value
        """
        ...
    
    @abstractmethod
    def extract_output_value(
        self,
        output: NodeOutputProtocol,
        output_name: str = "default"
    ) -> Any:
        """
        Extract a specific output value from a node output.
        
        Args:
            output: The node output object
            output_name: Name of the output to extract
            
        Returns:
            Extracted value
        """
        ...
    
    @abstractmethod
    def apply_transformation(
        self,
        value: Any,
        transformation_rules: dict[str, Any],
        source_context: dict[str, Any] | None = None
    ) -> Any:
        """
        Apply transformation rules to a value.
        
        Args:
            value: Value to transform
            transformation_rules: Rules from the edge
            source_context: Additional context for transformation
            
        Returns:
            Transformed value
        """
        ...
    
    @abstractmethod
    def register_transformation(
        self,
        name: str,
        rule: TransformationRule | Callable[[Any], Any]
    ) -> None:
        """
        Register a custom transformation rule.
        
        Args:
            name: Name of the transformation
            rule: Transformation rule or function
        """
        ...
    
    @abstractmethod
    def resolve_default_value(
        self,
        node: ExecutableNode,
        input_name: str,
        input_type: str | None = None
    ) -> Any:
        """
        Get default value for an unconnected input.
        
        Args:
            node: The node
            input_name: Name of the input
            input_type: Expected type of the input
            
        Returns:
            Default value or None
        """
        ...
    
    @abstractmethod
    def resolve_conditional_input(
        self,
        node: ExecutableNode,
        edges: list[ExecutableEdgeV2],
        context: ExecutionContext,
        condition_key: str = "is_conditional"
    ) -> dict[str, Any]:
        """
        Resolve inputs that depend on conditional branches.
        
        Args:
            node: Target node
            edges: Potential input edges
            context: Execution context with branch information
            condition_key: Key to check for conditional edges
            
        Returns:
            Resolved conditional inputs
        """
        ...
    
    @abstractmethod
    def validate_resolved_inputs(
        self,
        node: ExecutableNode,
        inputs: dict[str, Any]
    ) -> tuple[bool, list[str]]:
        """
        Validate that resolved inputs meet node requirements.
        
        Args:
            node: The node
            inputs: Resolved inputs
            
        Returns:
            Tuple of (is_valid, error_messages)
        """
        ...
    
    @abstractmethod
    def get_transformation_chain(
        self,
        source_type: str,
        target_type: str
    ) -> list[TransformationRule] | None:
        """
        Get chain of transformations to convert between types.
        
        Args:
            source_type: Source data type
            target_type: Target data type
            
        Returns:
            List of transformation rules or None if no path exists
        """
        ...