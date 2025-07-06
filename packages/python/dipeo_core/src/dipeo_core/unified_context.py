"""Unified execution context for DiPeO.

This module provides a single, consolidated execution context that replaces
the various context types (RuntimeContext, ExecutionContext, ExtendedExecutionContext)
with a unified implementation.
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Protocol

from dipeo_domain.models import DomainArrow, DomainDiagram, NodeOutput, TokenUsage
from dipeo_domain.handle_utils import extract_node_id_from_handle


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
    diagram: Optional[DomainDiagram] = None
    edges: List[Any] = field(default_factory=list)  # Can be dict or DomainArrow
    nodes: List[Any] = field(default_factory=list)  # Can be dict or DomainNode
    
    # Execution state
    node_outputs: Dict[str, Any] = field(default_factory=dict)
    node_states: Dict[str, Any] = field(default_factory=dict)
    exec_counts: Dict[str, int] = field(default_factory=dict)
    
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
    _token_accumulator: Dict[str, TokenUsage] = field(default_factory=dict, init=False)
    
    # Execution view (for view-based engine)
    _execution_view: Optional[Any] = field(default=None, init=False)
    
    # Node management methods
    def get_node_output(self, node_id: str) -> Any:
        """Get output for a node (supports both dict and NodeOutput)."""
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
    
    # Variable management
    def get_variable(self, name: str, default: Any = None) -> Any:
        return self.variables.get(name, default)
    
    def set_variable(self, name: str, value: Any) -> None:
        self.variables[name] = value
    
    # API key management
    def get_api_key(self, service: str) -> Optional[str]:
        """Get API key for a service."""
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
    def add_token_usage(self, node_id: str, tokens: TokenUsage) -> None:
        self._token_accumulator[node_id] = tokens
    
    def get_total_token_usage(self) -> TokenUsage:
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
        """Find edges originating from a node."""
        result = []
        for edge in self.edges:
            source = edge.get('source') if isinstance(edge, dict) else edge.source
            if source:
                edge_node_id = extract_node_id_from_handle(source)
                if edge_node_id == node_id:
                    result.append(edge)
        return result
    
    def find_edges_to(self, node_id: str) -> List[Any]:
        """Find edges targeting a node."""
        result = []
        for edge in self.edges:
            target = edge.get('target') if isinstance(edge, dict) else edge.target
            if target:
                edge_node_id = extract_node_id_from_handle(target)
                if edge_node_id == node_id:
                    result.append(edge)
        return result
    
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