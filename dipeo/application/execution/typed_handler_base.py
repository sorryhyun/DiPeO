# Type-safe handler system using generics

from abc import ABC, abstractmethod
from typing import Any, Dict, Generic, TypeVar, Type, Optional, TYPE_CHECKING

from pydantic import BaseModel

from dipeo.core.static.executable_diagram import ExecutableNode
from dipeo.core.static.generated_nodes import (
    PersonJobNode, ConditionNode, StartNode, EndpointNode,
    CodeJobNode, ApiJobNode, DBNode, HookNode, UserResponseNode, NotionNode
)
from dipeo.models import NodeOutput, NodeType

if TYPE_CHECKING:
    from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution
    from dipeo.application.execution.context.unified_execution_context import UnifiedExecutionContext

# Type variable for node types
T = TypeVar('T', bound=ExecutableNode)


class TypedNodeHandler(Generic[T], ABC):
    """Base class for type-safe node handlers using generics."""
    
    @property
    @abstractmethod
    def node_class(self) -> Type[T]:
        """The typed node class this handler handles."""
        pass
    
    @property
    @abstractmethod
    def node_type(self) -> str:
        """The node type string identifier."""
        pass
    
    @property
    @abstractmethod
    def schema(self) -> Type[BaseModel]:
        """The Pydantic schema for validation."""
        pass
    
    @property
    def requires_services(self) -> list[str]:
        """List of services required by this handler."""
        return []
    
    @property
    def description(self) -> str:
        """Description of this handler."""
        return f"Typed handler for {self.node_type} nodes"
    
    async def execute(
        self,
        props: BaseModel,
        context: "UnifiedExecutionContext",
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> NodeOutput:
        """Execute the handler with type-safe node."""
        # Extract typed node from services
        typed_node = services.get("typed_node")
        if not typed_node or not isinstance(typed_node, self.node_class):
            raise ValueError(f"Expected {self.node_class.__name__} but got {type(typed_node)}")
        
        # Delegate to typed execution
        return await self.execute_typed(
            node=typed_node,
            context=context,
            inputs=inputs,
            services=services
        )
    
    @abstractmethod
    async def execute_typed(
        self,
        node: T,
        context: "UnifiedExecutionContext",
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> NodeOutput:
        """Execute with strongly-typed node."""
        pass
    
    def to_node_handler(self):
        """Convert to node handler for compatibility with registry."""
        return self.execute
    
    def _get_execution(self, context: "UnifiedExecutionContext") -> "TypedStatefulExecution":
        """Get typed execution from context."""
        # The context should have access to the typed execution
        # This is a helper method to ensure type safety
        from dipeo.application.execution.stateful_execution_typed import TypedStatefulExecution
        
        # The execution state in context is managed by TypedStatefulExecution
        # We can reconstruct it or get it from the service registry
        service_registry = context.service_registry
        if service_registry:
            execution = service_registry.get('typed_execution')
            if isinstance(execution, TypedStatefulExecution):
                return execution
        
        raise ValueError("TypedStatefulExecution not found in context")
    
    def _build_output(
        self,
        value: Any,
        context: "UnifiedExecutionContext",
        metadata: Optional[Dict[str, Any]] = None
    ) -> NodeOutput:
        """Build a standard node output."""
        return NodeOutput(
            value=value,
            metadata=metadata or {},
            node_id=context.current_node_id,
            executed_nodes=context.executed_nodes
        )


# Concrete typed handler implementations

class TypedPersonJobHandler(TypedNodeHandler[PersonJobNode]):
    """Type-safe handler for PersonJobNode."""
    
    @property
    def node_class(self) -> Type[PersonJobNode]:
        return PersonJobNode
    
    @property
    def node_type(self) -> str:
        return NodeType.person_job.value
    
    @property
    def schema(self) -> Type[BaseModel]:
        from dipeo.models import PersonJobNodeData
        return PersonJobNodeData
    
    @property
    def requires_services(self) -> list[str]:
        return [
            "llm_service", 
            "diagram", 
            "conversation_service",
            "conversation_manager",
            "prompt_builder",
            "conversation_state_manager", 
            "memory_transformer"
        ]
    
    async def execute_typed(
        self,
        node: PersonJobNode,
        context: "UnifiedExecutionContext",
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> NodeOutput:
        """Execute PersonJobNode with full type safety."""
        # Direct access to typed properties
        person_id = node.person_id
        exec_count = context.get_node_execution_count(context.current_node_id)
        
        # Type-safe prompt selection
        if exec_count == 0 and node.first_only_prompt:
            prompt = node.first_only_prompt
        else:
            prompt = node.default_prompt
        
        # Direct access to tools
        if node.tools:
            # Handle tools with type safety
            pass
        
        # Direct access to memory config
        if node.memory_config:
            # Type-safe memory management
            forget_mode = node.memory_config.forget_mode
            max_messages = node.memory_config.max_messages
        
        # Continue with execution logic...
        # (Implementation would continue here)
        return self._build_output(
            {"default": ""},
            context,
            {"typed": True}
        )


class TypedConditionHandler(TypedNodeHandler[ConditionNode]):
    """Type-safe handler for ConditionNode."""
    
    @property
    def node_class(self) -> Type[ConditionNode]:
        return ConditionNode
    
    @property
    def node_type(self) -> str:
        return NodeType.condition.value
    
    @property
    def schema(self) -> Type[BaseModel]:
        from dipeo.models import ConditionNodeData
        return ConditionNodeData
    
    async def execute_typed(
        self,
        node: ConditionNode,
        context: "UnifiedExecutionContext",
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> NodeOutput:
        """Execute ConditionNode with type safety."""
        # Direct access to condition properties
        expression = node.expression
        condition_type = node.condition_type
        
        # Evaluate condition with type safety
        result = False  # Placeholder
        
        return self._build_output(
            {"default": result},
            context,
            {"expression": expression, "type": condition_type}
        )


class TypedEndpointHandler(TypedNodeHandler[EndpointNode]):
    """Type-safe handler for EndpointNode."""
    
    @property
    def node_class(self) -> Type[EndpointNode]:
        return EndpointNode
    
    @property
    def node_type(self) -> str:
        return NodeType.endpoint.value
    
    @property
    def schema(self) -> Type[BaseModel]:
        from dipeo.models import EndpointNodeData
        return EndpointNodeData
    
    async def execute_typed(
        self,
        node: EndpointNode,
        context: "UnifiedExecutionContext",
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> NodeOutput:
        """Execute EndpointNode with type safety."""
        # Direct access to save configuration
        if node.save_to_file:
            filename = node.file_name or f"output_{node.id}.json"
            # Save logic here
        
        return self._build_output(
            inputs,
            context,
            {"saved": node.save_to_file}
        )


class TypedCodeJobHandler(TypedNodeHandler[CodeJobNode]):
    """Type-safe handler for CodeJobNode."""
    
    @property
    def node_class(self) -> Type[CodeJobNode]:
        return CodeJobNode
    
    @property
    def node_type(self) -> str:
        return NodeType.code_job.value
    
    @property
    def schema(self) -> Type[BaseModel]:
        from dipeo.models import CodeJobNodeData
        return CodeJobNodeData
    
    @property
    def requires_services(self) -> list[str]:
        return ["code_execution_service"]
    
    async def execute_typed(
        self,
        node: CodeJobNode,
        context: "UnifiedExecutionContext",
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> NodeOutput:
        """Execute CodeJobNode with type safety."""
        # Direct access to code properties
        language = node.language
        code = node.code
        timeout = node.timeout
        
        # Execute code with type-safe configuration
        result = {"output": ""}  # Placeholder
        
        return self._build_output(
            result,
            context,
            {"language": language.value, "timeout": timeout}
        )


class TypedApiJobHandler(TypedNodeHandler[ApiJobNode]):
    """Type-safe handler for ApiJobNode."""
    
    @property
    def node_class(self) -> Type[ApiJobNode]:
        return ApiJobNode
    
    @property
    def node_type(self) -> str:
        return NodeType.api_job.value
    
    @property
    def schema(self) -> Type[BaseModel]:
        from dipeo.models import ApiJobNodeData
        return ApiJobNodeData
    
    @property
    def requires_services(self) -> list[str]:
        return ["http_client"]
    
    async def execute_typed(
        self,
        node: ApiJobNode,
        context: "UnifiedExecutionContext",
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> NodeOutput:
        """Execute ApiJobNode with type safety."""
        # Direct access to API properties
        url = node.url
        method = node.method
        headers = node.headers
        params = node.params
        body = node.body
        timeout = node.timeout
        auth_type = node.auth_type
        auth_config = node.auth_config
        
        # Make API call with type-safe configuration
        response = {"status": 200, "data": {}}  # Placeholder
        
        return self._build_output(
            response,
            context,
            {
                "url": url,
                "method": method.value if hasattr(method, 'value') else method,
                "status_code": response["status"]
            }
        )


class TypedStartHandler(TypedNodeHandler[StartNode]):
    """Type-safe handler for StartNode."""
    
    @property
    def node_class(self) -> Type[StartNode]:
        return StartNode
    
    @property
    def node_type(self) -> str:
        return NodeType.start.value
    
    @property
    def schema(self) -> Type[BaseModel]:
        from dipeo.models import StartNodeData
        return StartNodeData
    
    async def execute_typed(
        self,
        node: StartNode,
        context: "UnifiedExecutionContext",
        inputs: Dict[str, Any],
        services: Dict[str, Any]
    ) -> NodeOutput:
        """Execute StartNode with type safety."""
        # Direct access to start properties
        custom_data = node.custom_data
        output_structure = node.output_data_structure
        
        # Build output based on custom data
        output_value = {}
        for key, value in custom_data.items():
            output_value[key] = value
        
        return self._build_output(
            output_value,
            context,
            {"trigger_mode": node.trigger_mode}
        )


# Handler registry helpers

def create_typed_handler_registry() -> Dict[str, Type[TypedNodeHandler]]:
    """Create a registry of typed handlers."""
    return {
        NodeType.person_job.value: TypedPersonJobHandler,
        NodeType.condition.value: TypedConditionHandler,
        NodeType.endpoint.value: TypedEndpointHandler,
        NodeType.code_job.value: TypedCodeJobHandler,
        NodeType.api_job.value: TypedApiJobHandler,
        NodeType.start.value: TypedStartHandler,
    }


def register_typed_handlers(registry):
    """Register all typed handlers with the global registry."""
    typed_handlers = create_typed_handler_registry()
    
    for node_type, handler_class in typed_handlers.items():
        handler_instance = handler_class()
        registry.register(handler_instance)