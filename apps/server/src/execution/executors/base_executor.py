"""Base executor class for all node types."""

from abc import ABC, abstractmethod
from typing import Any, Dict, Tuple, Optional

from ..core.execution_context import ExecutionContext
from ..core.skip_manager import SkipManager


class BaseExecutor(ABC):
    """Abstract base class for all node executors.
    
    This provides a consistent interface for executing different node types
    while keeping the implementation simple and focused.
    """
    
    def __init__(self, context: ExecutionContext, llm_service=None, memory_service=None):
        """Initialize the base executor.
        
        Args:
            context: The execution context
            llm_service: Optional LLM service for nodes that need it
            memory_service: Optional memory service for nodes that need it
        """
        self.context = context
        self.llm_service = llm_service
        self.memory_service = memory_service
        self.node = None
        self.node_id = None
    
    async def validate_inputs(self, node: Dict[str, Any], context: ExecutionContext) -> Optional[str]:
        """Validate inputs for the node.
        
        Args:
            node: The node configuration
            context: The execution context
            
        Returns:
            Error message if validation fails, None if validation passes
        """
        # Default implementation - no validation
        return None
    
    @abstractmethod
    async def execute(
        self,
        node: Dict[str, Any],
        context: ExecutionContext,
        skip_manager: SkipManager,
        **kwargs
    ) -> Tuple[Any, float]:
        """Execute the node and return the result with cost.
        
        Args:
            node: The node configuration dictionary
            context: The execution context containing state
            skip_manager: The skip manager for handling skip logic
            **kwargs: Additional arguments specific to the executor
            
        Returns:
            A tuple of (output, cost) where:
                - output: The result of the node execution
                - cost: The cost associated with this execution
        """
        pass
    
    def _resolve_value(self, value: Any, context: ExecutionContext) -> Any:
        """Resolve a value that might contain references to other node outputs.
        
        Args:
            value: The value to resolve (might contain {{node_id}} references)
            context: The execution context containing node outputs
            
        Returns:
            The resolved value with all references replaced
        """
        if not isinstance(value, str):
            return value
        
        # Simple pattern matching for {{node_id}} references
        import re
        pattern = r'\{\{([^}]+)\}\}'
        
        def replace_reference(match):
            node_id = match.group(1).strip()
            output = context.get_node_output(node_id)
            return str(output) if output is not None else match.group(0)
        
        return re.sub(pattern, replace_reference, value)
    
    def _get_node_property(
        self,
        node: Dict[str, Any],
        property_path: str,
        default: Any = None
    ) -> Any:
        """Safely get a property from node data using dot notation.
        
        Args:
            node: The node configuration dictionary
            property_path: Dot-separated path to the property (e.g., "data.prompt")
            default: Default value if property not found
            
        Returns:
            The property value or default
        """
        try:
            value = node
            for key in property_path.split('.'):
                value = value.get(key, {})
            return value if value != {} else default
        except (AttributeError, TypeError):
            return default
    
    def _prepare_inputs(
        self,
        node: Dict[str, Any],
        context: ExecutionContext
    ) -> Dict[str, Any]:
        """Prepare and resolve all inputs for the node.
        
        Args:
            node: The node configuration dictionary
            context: The execution context containing state
            
        Returns:
            Dictionary of resolved inputs
        """
        inputs = {}
        node_data = node.get('data', {})
        
        # Resolve all string values that might contain references
        for key, value in node_data.items():
            inputs[key] = self._resolve_value(value, context)
        
        return inputs
    
    async def validate_inputs(
        self,
        node: Dict[str, Any],
        context: ExecutionContext
    ) -> Optional[str]:
        """Validate inputs before execution.
        
        Args:
            node: The node configuration dictionary
            context: The execution context containing state
            
        Returns:
            Error message if validation fails, None if valid
        """
        # Base implementation - can be overridden by subclasses
        return None
    
    def get_node_type(self) -> str:
        """Get the type of node this executor handles.
        
        Returns:
            The node type string
        """
        return self.__class__.__name__.replace('Executor', '').lower()
    
    def _get_person_property(
        self,
        person_id: str,
        property_path: str,
        default: Any = None
    ) -> Any:
        """Get a property from a person in the context.
        
        Args:
            person_id: The ID of the person
            property_path: Dot-separated path to the property (e.g., "data.llm")
            default: Default value if property not found
            
        Returns:
            The property value or default
        """
        if not self.context.diagram:
            return default
        
        persons = self.context.diagram.get('persons', {})
        person = persons.get(person_id)
        
        if not person:
            return default
        
        try:
            value = person
            for key in property_path.split('.'):
                value = value.get(key, {})
            return value if value != {} else default
        except (AttributeError, TypeError):
            return default