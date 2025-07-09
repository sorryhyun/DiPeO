"""Flow control ports for execution management.

These ports define the contracts for flow control operations that the domain layer
expects from the application layer implementations.
"""

from typing import Protocol, Dict, Any, List, Set, Optional
from abc import abstractmethod

from dipeo.models import DomainNode, DomainDiagram


class FlowDecisionPort(Protocol):
    """Port for flow control decisions."""
    
    @abstractmethod
    async def is_node_ready(
        self,
        node: DomainNode,
        diagram: DomainDiagram,
        executed_nodes: Set[str],
        node_outputs: Dict[str, Any],
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> bool:
        """Determine if a node is ready to execute."""
        ...
    
    @abstractmethod
    async def get_ready_nodes(
        self,
        diagram: DomainDiagram,
        executed_nodes: Set[str],
        node_outputs: Dict[str, Any],
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> List[DomainNode]:
        """Get all nodes that are ready to execute."""
        ...
    
    @abstractmethod
    async def should_execution_continue(
        self,
        ready_nodes: List[DomainNode],
        executed_nodes: Set[str],
        diagram: DomainDiagram,
        node_exec_counts: Optional[Dict[str, int]] = None,
    ) -> bool:
        """Determine if execution should continue."""
        ...
    
    @abstractmethod
    async def get_next_nodes(
        self,
        node_id: str,
        diagram: DomainDiagram,
        condition_result: Optional[bool] = None
    ) -> List[str]:
        """Get the next nodes to execute after a given node."""
        ...