"""Unified execution context for DiPeO.

This module provides a single, consolidated execution context that replaces
the various context types (RuntimeContext, ExecutionContext, ExtendedExecutionContext)
with a unified implementation.

NOTE: This class is now a facade that delegates to the new ApplicationExecutionContext.
It will be deprecated in a future release.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol, TYPE_CHECKING
import warnings
from datetime import datetime

# Note: Domain imports moved to lazy loading to respect architecture boundaries
# This class is deprecated and will be removed in future versions


class NodeHandler(Protocol):
    """Protocol for node handlers."""
    
    async def __call__(
        self,
        props: Any,
        context: "UnifiedExecutionContext",
        inputs: Dict[str, Any],
        services: Dict[str, Any],
    ) -> Any:
        ...


@dataclass
class UnifiedExecutionContext:
    """Unified execution context combining all previous context types.
    
    DEPRECATED: This class is now a facade that delegates to ApplicationExecutionContext.
    Use ExecutionContextPort or ApplicationExecutionContext directly for new code.
    
    This class consolidates:
    - RuntimeContext (for node handlers)
    - ExecutionContext (basic execution state)
    - ExtendedExecutionContext (token tracking)
    - Server-specific ExecutionContext (edge finding)
    """
    
    # Core identification
    execution_id: str
    diagram_id: str
    current_node_id: str = ""
    
    # Diagram structure
    diagram: Optional[Any] = None  # DomainDiagram - using Any to avoid domain dependency
    edges: List[Any] = field(default_factory=list)  # Can be dict or DomainArrow
    nodes: List[Any] = field(default_factory=list)  # Can be dict or DomainNode
    
    # Execution state
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    node_states: Dict[str, Any] = field(default_factory=dict)
    exec_counts: Dict[str, int] = field(default_factory=dict)
    executed_nodes: List[str] = field(default_factory=list)  # List of executed node IDs
    
    # Configuration
    variables: Dict[str, Any] = field(default_factory=dict)
    persons: Dict[str, Any] = field(default_factory=dict)
    api_keys: Dict[str, str] = field(default_factory=dict)
    
    # Services (optional, injected during execution)
    llm_service: Optional[Any] = None
    file_service: Optional[Any] = None
    notion_service: Optional[Any] = None
    conversation_service: Optional[Any] = None
    api_key_service: Optional[Any] = None
    state_store: Optional[Any] = None
    
    # Execution options
    interactive_handler: Optional[Callable] = None
    stream_callback: Optional[Callable] = None
    
    # Token usage tracking
    _token_accumulator: Dict[str, Any] = field(default_factory=dict, init=False)  # TokenUsage
    
    # Execution view (for view-based engine)
    _execution_view: Optional[Any] = field(default=None, init=False)
    
    # Internal: new context implementation (lazy-loaded)
    _app_context: Optional[Any] = field(default=None, init=False)
    _warned: bool = field(default=False, init=False)
    
    def _ensure_app_context(self) -> None:
        """Ensure the new ApplicationExecutionContext is initialized."""
        if not self._warned:
            warnings.warn(
                "UnifiedExecutionContext is deprecated. "
                "Use ApplicationExecutionContext for new code.",
                DeprecationWarning,
                stacklevel=3
            )
            self._warned = True
        
        if self._app_context is None:
            # Import here to avoid circular dependency
            from ..context.application_execution_context import ApplicationExecutionContext
            
            # Convert current state to ExecutionState
            execution_state = self._to_execution_state()
            
            # Create a simple service registry from current services
            service_registry = type('ServiceRegistry', (), {
                'llm_service': self.llm_service,
                'file_service': self.file_service,
                'notion_service': self.notion_service,
                'conversation_service': self.conversation_service,
                'api_key_service': self.api_key_service,
                'state_store': self.state_store,
            })()
            
            self._app_context = ApplicationExecutionContext(execution_state, service_registry)
    
    def _to_execution_state(self) -> Any:  # Returns ExecutionState
        """Convert current context to ExecutionState."""
        # Lazy import to avoid circular dependency
        from dipeo.models import ExecutionState, NodeState, NodeOutput
        
        # Convert node_states to proper format
        node_states = {}
        for node_id, state in self.node_states.items():
            if isinstance(state, dict):
                node_states[node_id] = NodeState(**state)
            else:
                node_states[node_id] = state
        
        # Convert node_outputs to proper format
        node_outputs = {}
        for node_id, output in self.node_outputs.items():
            if isinstance(output, NodeOutput):
                node_outputs[node_id] = output
            elif isinstance(output, dict) and 'value' in output:
                node_outputs[node_id] = NodeOutput(**output)
            else:
                node_outputs[node_id] = NodeOutput(value=output)
        
        from dipeo.models import ExecutionStatus
        
        return ExecutionState(
            id=self.execution_id,
            status=ExecutionStatus.RUNNING,
            diagram_id=self.diagram_id,
            started_at=datetime.now().isoformat(),
            node_states=node_states,
            node_outputs=node_outputs,
            token_usage=self.get_total_token_usage(),
            variables=self.variables,
            is_active=True
        )
    
    # Node management methods
    def get_node_output(self, node_id: str) -> Any:
        """Get output for a node (supports both dict and NodeOutput)."""
        # Use legacy implementation for now to avoid circular updates
        output = self.node_outputs.get(node_id)
        if hasattr(output, 'value'):
            return output.value
        return output
    
    def set_node_output(self, node_id: str, output: Any) -> None:
        self.node_outputs[node_id] = output
    
    def get_node_execution_count(self, node_id: str) -> int:
        return self.exec_counts.get(node_id, 0)
    
    def increment_node_execution_count(self, node_id: str) -> int:
        """Increment and return execution count for a node."""
        self.exec_counts[node_id] = self.exec_counts.get(node_id, 0) + 1
        return self.exec_counts[node_id]
    
    # Service management
    def get_service(self, service_name: str) -> Optional[Any]:
        """Get a service by name from the context."""
        # Map service names to attributes
        service_map = {
            'llm': self.llm_service,
            'llm_service': self.llm_service,
            'file': self.file_service,
            'file_service': self.file_service,
            'notion': self.notion_service,
            'notion_service': self.notion_service,
            'conversation': self.conversation_service,
            'conversation_service': self.conversation_service,
            'api_key': self.api_key_service,
            'api_key_service': self.api_key_service,
            'state_store': self.state_store,
        }
        return service_map.get(service_name)
    
    @property
    def execution_state(self) -> Any:  # Returns ExecutionState
        """Get the current execution state."""
        return self._to_execution_state()
    
    # Variable management
    def get_variable(self, name: str, default: Any = None) -> Any:
        """Get a variable from the context."""
        # Use legacy implementation to avoid circular updates
        return self.variables.get(name, default)
    
    def set_variable(self, name: str, value: Any) -> None:
        self.variables[name] = value
    
    # API key management
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a service."""
        self._ensure_app_context()
        if self.api_key_service:
            return self.api_key_service.get_api_key(service)
        return self.api_keys.get(service)
    
    # Conversation management
    def get_conversation_history(self, person_id: str) -> List[Dict[str, Any]]:
        """Get conversation history for a person."""
        return self.persons.get(person_id, [])
    
    def add_to_conversation(self, person_id: str, message: Dict[str, Any]) -> None:
        """Add message to conversation history."""
        if person_id not in self.persons:
            self.persons[person_id] = []
        self.persons[person_id].append(message)
    
    # Token usage tracking
    def add_token_usage(self, node_id: str, tokens: Any) -> None:  # tokens: TokenUsage
        self._token_accumulator[node_id] = tokens
    
    def get_total_token_usage(self) -> Any:  # Returns TokenUsage
        from dipeo.models import TokenUsage
        
        if not self._token_accumulator:
            return TokenUsage(input=0, output=0, total=0)
        
        total = TokenUsage(input=0, output=0, total=0)
        for tokens in self._token_accumulator.values():
            total.input += tokens.input
            total.output += tokens.output
            total.total += tokens.total
            if tokens.cached:
                total.cached = (total.cached or 0) + tokens.cached
        return total
    
    # Edge finding methods
    def find_edges_from(self, node_id: str) -> List[Any]:
        """Find edges originating from a node.
        
        DEPRECATED: Use dipeo.diagram.graph_utils.find_edges_from() instead.
        """
        from ...diagram.graph_utils import find_edges_from
        return find_edges_from(self.edges, node_id)
    
    def find_edges_to(self, node_id: str) -> List[Any]:
        """Find edges targeting a node.
        
        DEPRECATED: Use dipeo.diagram.graph_utils.find_edges_to() instead.
        """
        from ...diagram.graph_utils import find_edges_to
        return find_edges_to(self.edges, node_id)
    
    # Backward compatibility methods
    @property
    def outputs(self) -> Dict[str, Any]:
        """Legacy property for compatibility."""
        return {k: v.value if hasattr(v, 'value') else v 
                for k, v in self.node_outputs.items()}
    
    @property
    def exec_cnt(self) -> Dict[str, int]:
        """Legacy property for compatibility."""
        return self.exec_counts
    
    def increment_exec_count(self, node_id: str) -> int:
        """Legacy method for compatibility."""
        return self.increment_node_execution_count(node_id)


# Conversion functions removed - RuntimeContext is no longer supported