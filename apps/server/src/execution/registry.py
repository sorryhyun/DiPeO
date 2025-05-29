"""Node executor registry for managing node type to executor mappings."""

from typing import Dict, Type, Optional

from .nodes.base import BaseNodeExecutor
from .nodes import (
    PersonJobNodeExecutor,
    ConditionNodeExecutor,
    DBNodeExecutor,
    JobNodeExecutor,
    StartNodeExecutor,
    EndpointNodeExecutor
)
from ..constants import NodeType


class NodeExecutorRegistry:
    """Registry for mapping node types to their executor classes.
    
    Provides a centralized place to register and retrieve node executors,
    supporting both enum-based and legacy string-based node types.
    """
    
    def __init__(self):
        self._executors: Dict[str, Type[BaseNodeExecutor]] = {}
        self._register_default_executors()
    
    def _register_default_executors(self):
        """Register all built-in node executors."""
        # Register using NodeType enum values
        self.register(NodeType.PERSON_JOB.value, PersonJobNodeExecutor)
        self.register(NodeType.CONDITION.value, ConditionNodeExecutor)
        self.register(NodeType.DB.value, DBNodeExecutor)
        self.register(NodeType.JOB.value, JobNodeExecutor)
        self.register(NodeType.START.value, StartNodeExecutor)
        self.register(NodeType.ENDPOINT.value, EndpointNodeExecutor)
        
        # Also register legacy string names for backward compatibility
        self.register("personjobNode", PersonJobNodeExecutor)
        self.register("conditionNode", ConditionNodeExecutor)
        self.register("dbNode", DBNodeExecutor)
        self.register("jobNode", JobNodeExecutor)
        self.register("startNode", StartNodeExecutor)
        self.register("endpointNode", EndpointNodeExecutor)
    
    def register(self, node_type: str, executor_class: Type[BaseNodeExecutor]):
        """Register a node executor for a given node type.
        
        Args:
            node_type: The node type identifier
            executor_class: The executor class to handle this node type
        """
        self._executors[node_type] = executor_class
    
    def get_executor_class(self, node_type: str) -> Optional[Type[BaseNodeExecutor]]:
        """Get the executor class for a node type.
        
        Args:
            node_type: The node type identifier
            
        Returns:
            The executor class or None if not found
        """
        # First try direct lookup
        if node_type in self._executors:
            return self._executors[node_type]
        
        # Try converting from legacy format
        try:
            ntype = NodeType.from_legacy(node_type)
            return self._executors.get(ntype.value)
        except ValueError:
            return None
    
    def create_executor(
        self, 
        node_type: str,
        llm_service=None,
        memory_service=None,
        execution_id=None
    ) -> Optional[BaseNodeExecutor]:
        """Create an executor instance for a node type.
        
        Args:
            node_type: The node type identifier
            llm_service: LLM service instance
            memory_service: Memory service instance
            execution_id: Execution ID
            
        Returns:
            Executor instance or None if type not found
        """
        executor_class = self.get_executor_class(node_type)
        if not executor_class:
            return None
            
        return executor_class(
            llm_service=llm_service,
            memory_service=memory_service,
            execution_id=execution_id
        )
    
    def list_registered_types(self) -> list:
        """Get list of all registered node types."""
        return list(self._executors.keys())


# Global registry instance
node_executor_registry = NodeExecutorRegistry()