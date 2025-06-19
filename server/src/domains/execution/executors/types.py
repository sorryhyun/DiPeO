"""Core type definitions and protocols for the unified executor system."""

from typing import Protocol, Type, Dict, Any, List, Optional
from dataclasses import dataclass, field
from pydantic import BaseModel
from datetime import datetime
from src.__generated__.models import (
    TokenUsage,
    ExecutorResult as GeneratedExecutorResult,
    NodeDefinition as GeneratedNodeDefinition,
    ExecutionContext as GeneratedExecutionContext,
    PersonJobOutput as GeneratedPersonJobOutput,
    ConditionOutput as GeneratedConditionOutput,
    JobOutput as GeneratedJobOutput
)


# ExecutorResult is kept as dataclass for internal use
# If you need Pydantic validation, use GeneratedExecutorResult
@dataclass
class ExecutorResult:
    """Result from executor execution."""
    output: Any = None
    error: Optional[str] = None
    node_id: Optional[str] = None
    execution_time: Optional[float] = None
    token_usage: Optional[TokenUsage] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    validation_errors: List[Dict[str, Any]] = field(default_factory=list)


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


# NodeDefinition is kept as dataclass because it contains
# runtime handler references which can't be serialized
@dataclass
class NodeDefinition:
    """Definition of a node type."""
    type: str
    schema: Type[BaseModel]
    handler: NodeHandler
    requires_services: List[str] = field(default_factory=list)
    description: str = ""



# ExecutionContext is kept as dataclass because it contains
# runtime service references and methods
@dataclass
class ExecutionContext:
    """Simplified execution context for handlers."""
    edges: List[Dict[str, Any]]
    results: Dict[str, Dict[str, Any]]
    current_node_id: str
    execution_id: str
    exec_cnt: Dict[str, int] = field(default_factory=dict)  # Node execution counts
    outputs: Dict[str, Any] = field(default_factory=dict)   # Node outputs
    persons: Dict[str, Any] = field(default_factory=dict)   # Person configurations
    api_keys: Dict[str, str] = field(default_factory=dict)  # API keys
    
    # Services are accessed via attributes for backward compatibility
    llm_service: Optional[Any] = None
    memory_service: Optional[Any] = None
    person_service: Optional[Any] = None
    code_execution_service: Optional[Any] = None
    file_service: Optional[Any] = None
    notion_service: Optional[Any] = None
    user_interaction_service: Optional[Any] = None
    interactive_handler: Optional[Any] = None
    graph: Optional[Any] = None  # For graph operations
    
    def get_node_execution_count(self, node_id: str) -> int:
        """Get execution count for a specific node."""
        return self.exec_cnt.get(node_id, 0)
    
    def increment_node_execution_count(self, node_id: str) -> None:
        """Increment execution count for a specific node."""
        self.exec_cnt[node_id] = self.exec_cnt.get(node_id, 0) + 1


# Output types - use generated versions
PersonJobOutput = GeneratedPersonJobOutput
ConditionOutput = GeneratedConditionOutput
JobOutput = GeneratedJobOutput