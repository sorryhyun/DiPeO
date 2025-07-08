"""Value objects for the domain layer."""

from typing import Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


@dataclass(frozen=True)
class NodeExecutionContext:
    """Immutable context for node execution."""
    node_id: str
    node_type: str
    execution_count: int
    inputs: dict[str, Any]
    diagram_id: str
    execution_id: str
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def with_inputs(self, new_inputs: dict[str, Any]) -> 'NodeExecutionContext':
        """Create new context with updated inputs."""
        return NodeExecutionContext(
            node_id=self.node_id,
            node_type=self.node_type,
            execution_count=self.execution_count,
            inputs=new_inputs,
            diagram_id=self.diagram_id,
            execution_id=self.execution_id,
            timestamp=self.timestamp
        )


@dataclass(frozen=True)
class ExecutionResult:
    """Immutable result of an execution."""
    success: bool
    value: Any
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    duration_ms: Optional[float] = None
    
    @property
    def failed(self) -> bool:
        """Check if execution failed."""
        return not self.success


@dataclass(frozen=True)
class ValidationResult:
    """Immutable result of validation."""
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    
    @property
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    @property
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def merge(self, other: 'ValidationResult') -> 'ValidationResult':
        """Merge with another validation result."""
        return ValidationResult(
            valid=self.valid and other.valid,
            errors=self.errors + other.errors,
            warnings=self.warnings + other.warnings
        )


@dataclass(frozen=True)
class TransformationResult:
    """Immutable result of a transformation."""
    transformed_value: Any
    original_value: Any
    transformation_type: str
    metadata: dict[str, Any] = field(default_factory=dict)
    
    @property
    def changed(self) -> bool:
        """Check if value was changed."""
        return self.transformed_value != self.original_value


class MemoryScope(Enum):
    """Scope for memory/conversation context."""
    NODE = "node"          # Only within current node
    DIAGRAM = "diagram"    # Across diagram execution
    GLOBAL = "global"      # Across all executions
    SESSION = "session"    # Within a session


@dataclass(frozen=True)
class MemoryEntry:
    """Immutable memory entry."""
    key: str
    value: Any
    scope: MemoryScope
    timestamp: datetime = field(default_factory=datetime.utcnow)
    ttl_seconds: Optional[int] = None
    
    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.ttl_seconds is None:
            return False
        
        age = (datetime.utcnow() - self.timestamp).total_seconds()
        return age > self.ttl_seconds


@dataclass(frozen=True)
class APIRequest:
    """Immutable API request configuration."""
    url: str
    method: str
    headers: dict[str, str] = field(default_factory=dict)
    body: Optional[Any] = None
    timeout_seconds: int = 30
    retry_count: int = 0
    
    def with_header(self, key: str, value: str) -> 'APIRequest':
        """Create new request with additional header."""
        new_headers = self.headers.copy()
        new_headers[key] = value
        return APIRequest(
            url=self.url,
            method=self.method,
            headers=new_headers,
            body=self.body,
            timeout_seconds=self.timeout_seconds,
            retry_count=self.retry_count
        )


@dataclass(frozen=True)
class ConversationTurn:
    """Immutable conversation turn."""
    role: str
    content: str
    name: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_message_dict(self) -> dict[str, Any]:
        """Convert to message dictionary."""
        msg = {"role": self.role, "content": self.content}
        if self.name:
            msg["name"] = self.name
        return msg