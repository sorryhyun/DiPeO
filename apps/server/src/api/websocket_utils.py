"""WebSocket utilities for validation and message handling."""
from typing import Dict, Tuple, Optional, Any
from datetime import datetime

from .messages import ErrorMessage, MessageFactory


class WebSocketValidator:
    """Validation utilities for WebSocket messages."""
    
    @staticmethod
    def validate_required_fields(message: Dict[str, Any], fields: list) -> Optional[ErrorMessage]:
        """Validate that all required fields are present in message."""
        missing_fields = [field for field in fields if not message.get(field)]
        if missing_fields:
            return ErrorMessage(
                message=f"{', '.join(missing_fields)} {'is' if len(missing_fields) == 1 else 'are'} required"
            )
        return None
    
    @staticmethod
    def validate_node_control(message: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[ErrorMessage]]:
        """Validate node control messages and return node_id, execution_id, or error."""
        error = WebSocketValidator.validate_required_fields(message, ['nodeId', 'executionId'])
        if error:
            return None, None, error
        
        return message['nodeId'], message['executionId'], None
    
    @staticmethod
    def validate_execution_control(message: Dict[str, Any]) -> Tuple[Optional[str], Optional[ErrorMessage]]:
        """Validate execution control messages and return execution_id or error."""
        error = WebSocketValidator.validate_required_fields(message, ['executionId'])
        if error:
            return None, error
        
        return message['executionId'], None
    
    @staticmethod
    def validate_interactive_response(message: Dict[str, Any]) -> Tuple[Optional[str], Optional[str], Optional[str], Optional[ErrorMessage]]:
        """Validate interactive response and return node_id, execution_id, response, or error."""
        error = WebSocketValidator.validate_required_fields(message, ['nodeId', 'executionId'])
        if error:
            return None, None, None, error
        
        # Response can be empty string, so we use get with default
        response = message.get('response', '')
        return message['nodeId'], message['executionId'], response, None
    
    @staticmethod
    def validate_diagram_request(message: Dict[str, Any]) -> Tuple[Optional[Dict], Optional[Dict], Optional[ErrorMessage]]:
        """Validate diagram execution request."""
        diagram = message.get('diagram')
        if not diagram:
            return None, None, ErrorMessage(message='No diagram provided')
        
        options = message.get('options', {})
        return diagram, options, None


class MessageBroadcaster:
    """Helper for sending and broadcasting messages."""
    
    def __init__(self, send_func, broadcast_func):
        """Initialize with send and broadcast functions."""
        self.send_func = send_func
        self.broadcast_func = broadcast_func
    
    async def send_error(self, client_id: str, message: str, execution_id: Optional[str] = None) -> None:
        """Send an error message to a client."""
        await self.send_func(client_id, MessageFactory.error(message, execution_id))
    
    async def send_and_broadcast(self, client_id: str, message: Dict[str, Any], execution_id: Optional[str] = None) -> None:
        """Send message to client and optionally broadcast to all subscribed clients."""
        await self.send_func(client_id, message)
        
        if execution_id:
            await self.broadcast_func(message, execution_id)
    
    async def broadcast_only(self, message: Dict[str, Any], execution_id: str) -> None:
        """Broadcast message to all clients subscribed to an execution."""
        await self.broadcast_func(message, execution_id)


def generate_execution_id() -> str:
    """Generate a unique execution ID."""
    return f"exec_{int(datetime.now().timestamp() * 1000)}"


def format_duration(seconds: float) -> str:
    """Format duration in seconds to human-readable string."""
    if seconds < 1:
        return f"{seconds * 1000:.0f}ms"
    elif seconds < 60:
        return f"{seconds:.1f}s"
    else:
        minutes = seconds / 60
        return f"{minutes:.1f}m"