"""WebSocket message dataclasses for type-safe message creation."""
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Optional, Dict, Any, List
from enum import Enum


class MessageType(str, Enum):
    """WebSocket message types."""
    # Connection management
    CONNECTED = "connected"
    HEARTBEAT = "heartbeat"
    HEARTBEAT_ACK = "heartbeat_ack"
    SUBSCRIBED = "subscribed"
    ERROR = "error"
    
    # Execution lifecycle
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETE = "execution_complete"
    EXECUTION_ABORTED = "execution_aborted"
    EXECUTION_ABORT_REQUESTED = "execution_abort_requested"
    EXECUTION_ERROR = "execution_error"
    
    # Node lifecycle
    NODE_START = "node_start"
    NODE_PROGRESS = "node_progress"
    NODE_COMPLETE = "node_complete"
    NODE_ERROR = "node_error"
    NODE_SKIPPED = "node_skipped"
    
    # Node control
    NODE_PAUSED = "node_paused"
    NODE_RESUMED = "node_resumed"
    NODE_SKIP_REQUESTED = "node_skip_requested"
    
    # Interactive
    INTERACTIVE_PROMPT = "interactive_prompt"
    INTERACTIVE_PROMPT_TIMEOUT = "interactive_prompt_timeout"
    INTERACTIVE_RESPONSE_RECEIVED = "interactive_response_received"


def _current_timestamp() -> str:
    """Get current timestamp in ISO format."""
    return datetime.now().isoformat()


@dataclass
class BaseMessage:
    """Base class for all WebSocket messages."""
    type: MessageType
    timestamp: str = field(default_factory=_current_timestamp)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary, excluding None values."""
        data = asdict(self)
        # Convert enum to string
        data['type'] = data['type'].value if isinstance(data['type'], MessageType) else data['type']
        # Remove None values
        return {k: v for k, v in data.items() if v is not None}


@dataclass
class ErrorMessage(BaseMessage):
    """Error message."""
    type: MessageType = field(default=MessageType.ERROR)
    message: str = ""
    execution_id: Optional[str] = None


@dataclass
class ConnectionMessage(BaseMessage):
    """Connection-related messages."""
    client_id: Optional[str] = None
    channel: Optional[str] = None


@dataclass
class ConnectedMessage(ConnectionMessage):
    """Client connected message."""
    type: MessageType = field(default=MessageType.CONNECTED)


@dataclass
class HeartbeatAckMessage(BaseMessage):
    """Heartbeat acknowledgment."""
    type: MessageType = field(default=MessageType.HEARTBEAT_ACK)


@dataclass
class SubscribedMessage(ConnectionMessage):
    """Subscription confirmation."""
    type: MessageType = field(default=MessageType.SUBSCRIBED)


@dataclass
class ExecutionMessage(BaseMessage):
    """Base class for execution-related messages."""
    execution_id: str = ""


@dataclass
class ExecutionStartedMessage(ExecutionMessage):
    """Execution started message."""
    type: MessageType = field(default=MessageType.EXECUTION_STARTED)
    total_nodes: Optional[int] = None


@dataclass
class ExecutionCompleteMessage(ExecutionMessage):
    """Execution completed message."""
    type: MessageType = field(default=MessageType.EXECUTION_COMPLETE)
    total_cost: Optional[float] = None
    duration: Optional[float] = None


@dataclass
class ExecutionAbortedMessage(ExecutionMessage):
    """Execution aborted message."""
    type: MessageType = field(default=MessageType.EXECUTION_ABORTED)


@dataclass
class ExecutionAbortRequestedMessage(ExecutionMessage):
    """Execution abort requested message."""
    type: MessageType = field(default=MessageType.EXECUTION_ABORT_REQUESTED)


@dataclass
class ExecutionErrorMessage(ExecutionMessage):
    """Execution error message."""
    type: MessageType = field(default=MessageType.EXECUTION_ERROR)
    error: str = ""


@dataclass
class NodeMessage(ExecutionMessage):
    """Base class for node-related messages."""
    node_id: str = ""


@dataclass
class NodeStartMessage(NodeMessage):
    """Node execution started."""
    type: MessageType = field(default=MessageType.NODE_START)
    node_type: Optional[str] = None


@dataclass
class NodeProgressMessage(NodeMessage):
    """Node execution progress update."""
    type: MessageType = field(default=MessageType.NODE_PROGRESS)
    message: str = ""


@dataclass
class NodeCompleteMessage(NodeMessage):
    """Node execution completed."""
    type: MessageType = field(default=MessageType.NODE_COMPLETE)
    output: Optional[Dict[str, Any]] = None
    cost: Optional[float] = None


@dataclass
class NodeErrorMessage(NodeMessage):
    """Node execution error."""
    type: MessageType = field(default=MessageType.NODE_ERROR)
    error: str = ""


@dataclass
class NodeSkippedMessage(NodeMessage):
    """Node execution skipped."""
    type: MessageType = field(default=MessageType.NODE_SKIPPED)
    reason: Optional[str] = None


@dataclass
class NodePausedMessage(NodeMessage):
    """Node paused message."""
    type: MessageType = field(default=MessageType.NODE_PAUSED)


@dataclass
class NodeResumedMessage(NodeMessage):
    """Node resumed message."""
    type: MessageType = field(default=MessageType.NODE_RESUMED)


@dataclass
class NodeSkipRequestedMessage(NodeMessage):
    """Node skip requested message."""
    type: MessageType = field(default=MessageType.NODE_SKIP_REQUESTED)


@dataclass
class InteractivePromptMessage(NodeMessage):
    """Interactive prompt request."""
    type: MessageType = field(default=MessageType.INTERACTIVE_PROMPT)
    prompt: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    timeout: Optional[int] = None


@dataclass
class InteractivePromptTimeoutMessage(NodeMessage):
    """Interactive prompt timeout."""
    type: MessageType = field(default=MessageType.INTERACTIVE_PROMPT_TIMEOUT)


@dataclass
class InteractiveResponseReceivedMessage(NodeMessage):
    """Interactive response received."""
    type: MessageType = field(default=MessageType.INTERACTIVE_RESPONSE_RECEIVED)


class MessageFactory:
    """Factory for creating WebSocket messages."""
    
    @staticmethod
    def error(message: str, execution_id: Optional[str] = None) -> Dict[str, Any]:
        """Create an error message."""
        return ErrorMessage(message=message, execution_id=execution_id).to_dict()
    
    @staticmethod
    def connected(client_id: str) -> Dict[str, Any]:
        """Create a connected message."""
        return ConnectedMessage(client_id=client_id).to_dict()
    
    @staticmethod
    def heartbeat_ack() -> Dict[str, Any]:
        """Create a heartbeat acknowledgment."""
        return HeartbeatAckMessage().to_dict()
    
    @staticmethod
    def subscribed(channel: str) -> Dict[str, Any]:
        """Create a subscription confirmation."""
        return SubscribedMessage(channel=channel).to_dict()
    
    @staticmethod
    def execution_started(execution_id: str, total_nodes: Optional[int] = None) -> Dict[str, Any]:
        """Create an execution started message."""
        return ExecutionStartedMessage(execution_id=execution_id, total_nodes=total_nodes).to_dict()
    
    @staticmethod
    def execution_complete(execution_id: str, total_cost: Optional[float] = None, 
                         duration: Optional[float] = None) -> Dict[str, Any]:
        """Create an execution complete message."""
        return ExecutionCompleteMessage(
            execution_id=execution_id, 
            total_cost=total_cost, 
            duration=duration
        ).to_dict()
    
    @staticmethod
    def node_paused(node_id: str, execution_id: str) -> Dict[str, Any]:
        """Create a node paused message."""
        return NodePausedMessage(node_id=node_id, execution_id=execution_id).to_dict()
    
    @staticmethod
    def node_resumed(node_id: str, execution_id: str) -> Dict[str, Any]:
        """Create a node resumed message."""
        return NodeResumedMessage(node_id=node_id, execution_id=execution_id).to_dict()
    
    @staticmethod
    def interactive_prompt(node_id: str, execution_id: str, prompt: str, 
                         context: Dict[str, Any], timeout: Optional[int] = None) -> Dict[str, Any]:
        """Create an interactive prompt message."""
        return InteractivePromptMessage(
            node_id=node_id,
            execution_id=execution_id,
            prompt=prompt,
            context=context,
            timeout=timeout
        ).to_dict()
    
    @staticmethod
    def node_skip_requested(node_id: str, execution_id: str) -> Dict[str, Any]:
        """Create a node skip requested message."""
        return NodeSkipRequestedMessage(node_id=node_id, execution_id=execution_id).to_dict()
    
    @staticmethod
    def execution_abort_requested(execution_id: str) -> Dict[str, Any]:
        """Create an execution abort requested message."""
        return ExecutionAbortRequestedMessage(execution_id=execution_id).to_dict()
    
    @staticmethod
    def execution_aborted(execution_id: str) -> Dict[str, Any]:
        """Create an execution aborted message."""
        return ExecutionAbortedMessage(execution_id=execution_id).to_dict()
    
    @staticmethod
    def interactive_response_received(node_id: str, execution_id: str) -> Dict[str, Any]:
        """Create an interactive response received message."""
        return InteractiveResponseReceivedMessage(node_id=node_id, execution_id=execution_id).to_dict()