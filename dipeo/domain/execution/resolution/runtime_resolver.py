"""Runtime input resolution interfaces.

This module provides the domain contracts for resolving actual input values
during diagram execution.
"""

from typing import Any
from abc import ABC, abstractmethod

from dipeo.diagram_generated import NodeID
from dipeo.domain.diagram.compilation import TransformRules


class RuntimeInputResolver(ABC):
    """Base class for resolving actual input values at runtime.
    
    This resolver works during diagram execution to provide actual values
    for node inputs based on outputs from previously executed nodes.
    """
    
    @abstractmethod
    async def resolve_input_value(
        self,
        target_node_id: NodeID,
        target_input: str,
        node_outputs: dict[NodeID, Any],
        transformation_rules: TransformRules | None = None
    ) -> Any:
        """Resolve the actual value for a node's input at runtime.
        
        Args:
            target_node_id: ID of the node needing input
            target_input: Name of the input to resolve
            node_outputs: Outputs from previously executed nodes
            transformation_rules: Optional transformation rules to apply
            
        Returns:
            The resolved input value
        """
        pass