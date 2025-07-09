"""Flow control services for execution management.

NOTE: This file was relocated from dipeo/core/ports/ during architectural cleanup.
It was moved because it represents internal domain logic for flow control decisions,
not an interface to external infrastructure (which is what true hexagonal ports are for).

These services define the contracts for flow control operations within the domain layer.
They handle execution flow decisions, node readiness checks, and execution path determination.
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