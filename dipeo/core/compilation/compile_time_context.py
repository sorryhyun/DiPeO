"""Protocol for compile-time context during diagram compilation."""

from abc import abstractmethod
from typing import Any, Protocol

from dipeo.diagram_generated import NodeID, NodeType
from dipeo.core.compilation.executable_diagram import ExecutableNode


class CompileTimeContext(Protocol):
    """Provides context and utilities during diagram compilation phase.
    
    This protocol defines the contract for managing compile-time information
    and transformations during the diagram compilation process.
    """
    
    # Node Registration
    
    @abstractmethod
    def register_node(self, node: ExecutableNode) -> None:
        """Register a node during compilation."""
        ...
    
    @abstractmethod
    def get_registered_nodes(self) -> list[ExecutableNode]:
        """Get all registered nodes."""
        ...
    
    @abstractmethod
    def get_nodes_by_type(self, node_type: NodeType) -> list[ExecutableNode]:
        """Get all nodes of a specific type."""
        ...
    
    # Validation Context
    
    @abstractmethod
    def add_validation_error(self, node_id: NodeID, error: str) -> None:
        """Add a validation error for a node."""
        ...
    
    @abstractmethod
    def add_validation_warning(self, node_id: NodeID, warning: str) -> None:
        """Add a validation warning for a node."""
        ...
    
    @abstractmethod
    def get_validation_errors(self) -> dict[NodeID, list[str]]:
        """Get all validation errors."""
        ...
    
    @abstractmethod
    def get_validation_warnings(self) -> dict[NodeID, list[str]]:
        """Get all validation warnings."""
        ...
    
    @abstractmethod
    def has_errors(self) -> bool:
        """Check if there are any validation errors."""
        ...
    
    # Compilation Metadata
    
    @abstractmethod
    def set_metadata(self, key: str, value: Any) -> None:
        """Set compilation metadata."""
        ...
    
    @abstractmethod
    def get_metadata(self, key: str) -> Any | None:
        """Get compilation metadata."""
        ...
    
    @abstractmethod
    def get_all_metadata(self) -> dict[str, Any]:
        """Get all compilation metadata."""
        ...
    
    # Interface Resolution Context
    
    @abstractmethod
    def register_interface(self, node_id: NodeID, interface_name: str, interface_type: str) -> None:
        """Register an interface provided by a node."""
        ...
    
    @abstractmethod
    def get_interface_providers(self, interface_type: str) -> list[tuple[NodeID, str]]:
        """Get all nodes that provide a specific interface type."""
        ...
    
    @abstractmethod
    def get_node_interfaces(self, node_id: NodeID) -> dict[str, str]:
        """Get all interfaces provided by a node."""
        ...
    
    # Dependency Tracking
    
    @abstractmethod
    def add_node_dependency(self, node_id: NodeID, depends_on: NodeID, dependency_type: str = "data") -> None:
        """Add a dependency between nodes."""
        ...
    
    @abstractmethod
    def get_node_dependencies(self, node_id: NodeID) -> list[tuple[NodeID, str]]:
        """Get all dependencies of a node."""
        ...
    
    @abstractmethod
    def get_node_dependents(self, node_id: NodeID) -> list[NodeID]:
        """Get all nodes that depend on a given node."""
        ...
    
    # Optimization Hints
    
    @abstractmethod
    def mark_node_parallelizable(self, node_id: NodeID) -> None:
        """Mark a node as safe for parallel execution."""
        ...
    
    @abstractmethod
    def mark_node_cacheable(self, node_id: NodeID, cache_key: str | None = None) -> None:
        """Mark a node's output as cacheable."""
        ...
    
    @abstractmethod
    def get_parallelizable_nodes(self) -> set[NodeID]:
        """Get all nodes marked as parallelizable."""
        ...
    
    @abstractmethod
    def get_cacheable_nodes(self) -> dict[NodeID, str | None]:
        """Get all nodes marked as cacheable with their cache keys."""
        ...