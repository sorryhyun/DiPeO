from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
import re
import logging

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of node validation"""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ExecutorResult:
    """Result from executor execution"""
    output: Any
    metadata: Dict[str, Any] = field(default_factory=dict)
    cost: float = 0.0
    tokens_used: Optional[Dict[str, int]] = None
    error: Optional[str] = None
    execution_time: float = 0.0


class BaseExecutor(ABC):
    """
    Base class for all node executors.
    Provides common functionality for validation, execution, and utilities.
    """
    
    def __init__(self):
        self.logger = logger
    
    @abstractmethod
    async def validate(self, node: Dict[str, Any], context: 'ExecutionContext') -> ValidationResult:
        """
        Validate node configuration before execution.
        
        Args:
            node: The node to validate
            context: Current execution context
            
        Returns:
            ValidationResult with validity status and any errors/warnings
        """
        pass
    
    @abstractmethod
    async def execute(self, node: Dict[str, Any], context: 'ExecutionContext') -> ExecutorResult:
        """
        Execute the node and return results.
        
        Args:
            node: The node to execute
            context: Current execution context
            
        Returns:
            ExecutorResult with output and metadata
        """
        pass
    
    def get_node_type(self) -> str:
        """
        Get the node type this executor handles.
        By convention, uses the class name without 'Executor' suffix.
        """
        class_name = self.__class__.__name__
        if class_name.endswith('Executor'):
            return class_name[:-8].lower()
        return class_name.lower()
    
    def get_input_values(self, node: Dict[str, Any], context: 'ExecutionContext') -> Dict[str, Any]:
        """
        Get input values for a node from incoming arrows.
        
        Args:
            node: The node to get inputs for
            context: Execution context with arrow information
            
        Returns:
            Dictionary mapping arrow labels to their values
        """
        inputs = {}
        node_id = node["id"]
        incoming = context.incoming_arrows.get(node_id, [])
        
        for arrow in incoming:
            source_id = arrow["source"]
            label = arrow.get("label", "")
            
            # Get the output from the source node
            if source_id in context.node_outputs and label:
                inputs[label] = context.node_outputs[source_id]
        
        return inputs
    
    def substitute_variables(self, text: str, variables: Dict[str, Any]) -> str:
        """
        Substitute {{variable}} patterns in text.
        
        Args:
            text: Text containing variable placeholders
            variables: Dictionary of variable values
            
        Returns:
            Text with variables substituted
        """
        if not text:
            return text
        
        def replace_var(match):
            var_name = match.group(1)
            value = variables.get(var_name, match.group(0))
            # Convert to string, handling special cases
            if value is None:
                return ""
            elif isinstance(value, bool):
                return str(value).lower()
            else:
                return str(value)
        
        # Replace {{variable}} patterns
        return re.sub(r'\{\{(\w+)\}\}', replace_var, text)
    
    def validate_required_properties(
        self, 
        node: Dict[str, Any], 
        required_props: List[str]
    ) -> ValidationResult:
        """
        Validate that required properties exist in the node.
        
        Args:
            node: The node to validate
            required_props: List of required property names
            
        Returns:
            ValidationResult
        """
        errors = []
        properties = node.get("properties", {})
        
        for prop in required_props:
            if prop not in properties or properties[prop] is None:
                errors.append(f"Required property '{prop}' is missing")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )
    
    def validate_property_types(
        self,
        node: Dict[str, Any],
        type_specs: Dict[str, type]
    ) -> ValidationResult:
        """
        Validate property types match expected types.
        
        Args:
            node: The node to validate
            type_specs: Dictionary mapping property names to expected types
            
        Returns:
            ValidationResult
        """
        errors = []
        warnings = []
        properties = node.get("properties", {})
        
        for prop_name, expected_type in type_specs.items():
            if prop_name in properties:
                value = properties[prop_name]
                if value is not None and not isinstance(value, expected_type):
                    # Try type coercion for common cases
                    if expected_type == int and isinstance(value, str):
                        try:
                            int(value)
                            warnings.append(f"Property '{prop_name}' will be converted from string to int")
                        except ValueError:
                            errors.append(f"Property '{prop_name}' must be of type {expected_type.__name__}")
                    elif expected_type == float and isinstance(value, (int, str)):
                        try:
                            float(value)
                            warnings.append(f"Property '{prop_name}' will be converted to float")
                        except ValueError:
                            errors.append(f"Property '{prop_name}' must be of type {expected_type.__name__}")
                    else:
                        errors.append(f"Property '{prop_name}' must be of type {expected_type.__name__}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors,
            warnings=warnings
        )
    
    def has_incoming_connection(self, node: Dict[str, Any], context: 'ExecutionContext') -> bool:
        """Check if node has any incoming connections"""
        node_id = node["id"]
        return node_id in context.incoming_arrows and len(context.incoming_arrows[node_id]) > 0
    
    def has_outgoing_connection(self, node: Dict[str, Any], context: 'ExecutionContext') -> bool:
        """Check if node has any outgoing connections"""
        node_id = node["id"]
        return node_id in context.outgoing_arrows and len(context.outgoing_arrows[node_id]) > 0
    
    def get_upstream_nodes(self, node: Dict[str, Any], context: 'ExecutionContext') -> List[str]:
        """Get IDs of all upstream (source) nodes"""
        node_id = node["id"]
        upstream = []
        
        for arrow in context.incoming_arrows.get(node_id, []):
            source_id = arrow["source"]
            if source_id not in upstream:
                upstream.append(source_id)
        
        return upstream
    
    def get_downstream_nodes(self, node: Dict[str, Any], context: 'ExecutionContext') -> List[str]:
        """Get IDs of all downstream (target) nodes"""
        node_id = node["id"]
        downstream = []
        
        for arrow in context.outgoing_arrows.get(node_id, []):
            target_id = arrow["target"]
            if target_id not in downstream:
                downstream.append(target_id)
        
        return downstream


class ClientSafeExecutor(BaseExecutor):
    """
    Base class for executors that can run safely on the client side.
    These executors should not access external resources or sensitive operations.
    """
    
    def is_client_safe(self) -> bool:
        """Indicates this executor is safe for client-side execution"""
        return True


class ServerOnlyExecutor(BaseExecutor):
    """
    Base class for executors that must run on the server.
    These executors may access external APIs, databases, or file systems.
    """
    
    def is_client_safe(self) -> bool:
        """Indicates this executor requires server-side execution"""
        return False
    
    async def check_api_keys(self, required_keys: List[str], context: 'ExecutionContext') -> ValidationResult:
        """
        Check if required API keys are available.
        
        Args:
            required_keys: List of required API key names
            context: Execution context
            
        Returns:
            ValidationResult
        """
        errors = []
        
        # Check API keys from context or environment
        api_keys = context.api_keys if hasattr(context, 'api_keys') else {}
        
        for key_name in required_keys:
            if key_name not in api_keys or not api_keys[key_name]:
                errors.append(f"Missing required API key: {key_name}")
        
        return ValidationResult(
            is_valid=len(errors) == 0,
            errors=errors
        )


class ExecutorFactory:
    """
    Factory for creating executor instances based on node type.
    """
    
    def __init__(self):
        self._executors: Dict[str, BaseExecutor] = {}
        self.logger = logger
    
    def register_executor(self, node_type: str, executor: BaseExecutor) -> None:
        """
        Register an executor for a specific node type.
        
        Args:
            node_type: The node type this executor handles
            executor: The executor instance
        """
        self._executors[node_type] = executor
        self.logger.info(f"Registered executor for node type: {node_type}")
    
    def get_executor(self, node_type: str) -> Optional[BaseExecutor]:
        """
        Get executor for a node type.
        
        Args:
            node_type: The node type
            
        Returns:
            Executor instance or None if not found
        """
        return self._executors.get(node_type)
    
    def create_executors(self, execution_strategy: str = "hybrid") -> Dict[str, BaseExecutor]:
        """
        Create executors based on execution strategy.
        
        Args:
            execution_strategy: One of "client", "server", or "hybrid"
            
        Returns:
            Dictionary mapping node types to executors
        """
        executors = {}
        
        # Register all available executors
        # This will be populated as concrete executors are implemented
        
        return executors
    
    def is_client_safe_node(self, node_type: str) -> bool:
        """Check if a node type can be executed client-side"""
        executor = self._executors.get(node_type)
        if executor and hasattr(executor, 'is_client_safe'):
            return executor.is_client_safe()
        return False