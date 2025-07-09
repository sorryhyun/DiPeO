"""Node execution services for handling individual node execution.

NOTE: This file was relocated from dipeo/core/ports/ during architectural cleanup.
It was moved because it represents core domain logic for node execution and diagram analysis,
not an interface to external infrastructure (which is what true hexagonal ports are for).

These services define the contracts for node-level execution operations and diagram analysis
within the domain layer.
"""

from typing import Protocol, Dict, Any, Optional, List
from abc import abstractmethod

from dipeo.models import DomainNode, DomainDiagram


class NodeExecutionPort(Protocol):
    """Port for node execution operations."""
    
    @abstractmethod
    async def execute_node(
        self,
        node: DomainNode,
        inputs: Dict[str, Any],
        context: Dict[str, Any],
    ) -> Any:
        """Execute a single node and return its output."""
        ...
    
    @abstractmethod
    async def can_node_execute(
        self,
        node: DomainNode,
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> bool:
        """Check if a node can execute based on its constraints."""
        ...


class DiagramAnalysisPort(Protocol):
    """Port for diagram analysis operations."""
    
    @abstractmethod
    async def validate_diagram(self, diagram: DomainDiagram) -> List[str]:
        """Validate a diagram and return any validation errors."""
        ...
    
    @abstractmethod
    async def find_execution_path(
        self,
        diagram: DomainDiagram,
        start_node_id: Optional[str] = None,
        end_node_id: Optional[str] = None
    ) -> List[str]:
        """Find a valid execution path through the diagram."""
        ...
    
    @abstractmethod
    async def get_node_dependencies(
        self,
        node: DomainNode,
        diagram: DomainDiagram,
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> List[str]:
        """Get all nodes that this node depends on."""
        ...