"""Core type definitions and protocols for the unified executor system."""

from typing import Protocol, Type, Dict, Any, List, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel
from datetime import datetime
from ...diagram.models.domain import TokenUsage


class ExecutorResult:
    """Result from executor execution."""
    def __init__(
        self,
        output: Any = None,
        error: Optional[str] = None,
        node_id: Optional[str] = None,
        execution_time: Optional[float] = None,
        token_usage: Optional[TokenUsage] = None,
        metadata: Optional[Dict[str, Any]] = None,
        validation_errors: Optional[List[Dict[str, Any]]] = None
    ):
        self.output = output
        self.error = error
        self.node_id = node_id
        self.execution_time = execution_time
        self.token_usage = token_usage
        self.metadata = metadata or {}
        self.validation_errors = validation_errors or []


class NodeHandler(Protocol):
    """Protocol for node handlers."""
    async def __call__(
        self, 
        props: BaseModel, 
        context: 'ExecutionContext', 
        inputs: Dict[str, Any]
    ) -> Any:
        """Execute the node handler with validated properties."""
        ...


@dataclass
class NodeDefinition:
    """Definition of a node type."""
    type: str
    schema: Type[BaseModel]
    handler: NodeHandler
    requires_services: List[str] = field(default_factory=list)
    description: str = ""


class Middleware(Protocol):
    """Protocol for execution middleware."""
    
    async def pre_execute(self, node: Dict[str, Any], context: 'ExecutionContext') -> None:
        """Called before node execution."""
        ...
    
    async def post_execute(
        self, 
        node: Dict[str, Any], 
        context: 'ExecutionContext', 
        result: ExecutorResult
    ) -> None:
        """Called after node execution."""
        ...


class ExecutionContext(Protocol):
    """Protocol for execution context provided to handlers."""
    
    @property
    def edges(self) -> List[Dict[str, Any]]:
        """Graph edges connecting nodes."""
        ...
    
    @property
    def results(self) -> Dict[str, Dict[str, Any]]:
        """Results from executed nodes."""
        ...
    
    @property
    def current_node_id(self) -> str:
        """ID of the currently executing node."""
        ...
    
    def get_node_execution_count(self, node_id: str) -> int:
        """Get execution count for a specific node."""
        ...
    
    def increment_node_execution_count(self, node_id: str) -> None:
        """Increment execution count for a specific node."""
        ...
    
    # Service protocols (to be expanded based on actual services)
    @property
    def llm_service(self) -> Any:
        """LLM service for AI calls."""
        ...
    
    @property
    def memory_service(self) -> Any:
        """Memory service for conversation history."""
        ...
    
    @property
    def person_service(self) -> Any:
        """Person service for managing person configurations."""
        ...
    
    @property
    def code_execution_service(self) -> Any:
        """Service for executing code in various languages."""
        ...
    
    @property
    def file_service(self) -> Any:
        """Service for file operations."""
        ...
    
    @property
    def notion_service(self) -> Any:
        """Service for Notion integration."""
        ...
    
    @property
    def user_interaction_service(self) -> Any:
        """Service for user interactions."""
        ...


# Output types for specific handlers
@dataclass
class PersonJobOutput:
    """Output from PersonJob handler."""
    output: Optional[str]
    error: Optional[str] = None
    conversation_history: List[Dict[str, str]] = field(default_factory=list)
    token_usage: Optional[TokenUsage] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ConditionOutput:
    """Output from Condition handler."""
    result: bool
    evaluated_expression: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class JobOutput:
    """Output from Job handler."""
    output: Any
    error: Optional[str] = None
    execution_time: float = 0.0
    language: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)