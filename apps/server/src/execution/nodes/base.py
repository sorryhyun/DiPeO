"""Base class for all node executors."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Tuple, Optional

from ..state import ExecutionState
from ...services.llm_service import LLMService
from ...services.memory_service import MemoryService


class BaseNodeExecutor(ABC):
    """Abstract base class for node executors.
    
    Each node type should implement this interface to handle
    its specific execution logic.
    """
    
    def __init__(self, 
                 llm_service: LLMService = None,
                 memory_service: MemoryService = None,
                 execution_id: str = None):
        """Initialize node executor with optional services.
        
        Args:
            llm_service: Service for LLM interactions
            memory_service: Service for memory/conversation management
            execution_id: Unique ID for this execution run
        """
        self.llm_service = llm_service
        self.memory_service = memory_service
        self.execution_id = execution_id
    
    @abstractmethod
    async def execute(
        self, 
        node: dict, 
        vars_map: Dict[str, Any], 
        inputs: List[Any],
        state: ExecutionState,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute the node and return result and cost.
        
        Args:
            node: Node configuration including id, type, and data
            vars_map: Variable mappings for template resolution
            inputs: Input values from incoming arrows
            state: Current execution state
            **kwargs: Additional executor-specific arguments
            
        Returns:
            Tuple of (result, cost_in_usd)
        """
        pass
    
    def validate_inputs(self, node: dict, inputs: List[Any]) -> None:
        """Validate inputs for the node.
        
        Default implementation does nothing. Override for specific validation.
        
        Args:
            node: Node configuration
            inputs: Input values to validate
            
        Raises:
            ValueError: If inputs are invalid
        """
        pass
    
    def get_node_data(self, node: dict) -> dict:
        """Extract node data safely.
        
        Args:
            node: Node configuration
            
        Returns:
            Node data dictionary, empty dict if not present
        """
        return node.get("data", {})
    
    def get_node_id(self, node: dict) -> Optional[str]:
        """Extract node ID safely.
        
        Args:
            node: Node configuration
            
        Returns:
            Node ID or None if not present
        """
        return node.get("id")