"""Message role value object."""
from dataclasses import dataclass
from enum import Enum


class MessageRoleType(Enum):
    """Supported message roles in conversations."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    FUNCTION = "function"
    TOOL = "tool"


@dataclass(frozen=True)
class MessageRole:
    """Represents a role in a conversation message."""
    
    value: MessageRoleType
    
    @classmethod
    def from_string(cls, role_str: str) -> 'MessageRole':
        """Create from string representation."""
        try:
            role_type = MessageRoleType(role_str.lower())
            return cls(value=role_type)
        except ValueError:
            raise ValueError(f"Invalid message role: {role_str}")
    
    @property
    def is_user(self) -> bool:
        """Check if this is a user role."""
        return self.value == MessageRoleType.USER
    
    @property
    def is_assistant(self) -> bool:
        """Check if this is an assistant role."""
        return self.value == MessageRoleType.ASSISTANT
    
    @property
    def is_system(self) -> bool:
        """Check if this is a system role."""
        return self.value == MessageRoleType.SYSTEM
    
    @property
    def is_function(self) -> bool:
        """Check if this is a function role."""
        return self.value == MessageRoleType.FUNCTION
    
    @property
    def is_tool(self) -> bool:
        """Check if this is a tool role."""
        return self.value == MessageRoleType.TOOL
    
    @property
    def is_ai_generated(self) -> bool:
        """Check if this role represents AI-generated content."""
        return self.value in {MessageRoleType.ASSISTANT, MessageRoleType.FUNCTION, MessageRoleType.TOOL}
    
    @property
    def is_human_generated(self) -> bool:
        """Check if this role represents human-generated content."""
        return self.value == MessageRoleType.USER
    
    @property
    def display_name(self) -> str:
        """Get a human-friendly display name."""
        display_names = {
            MessageRoleType.USER: "User",
            MessageRoleType.ASSISTANT: "Assistant",
            MessageRoleType.SYSTEM: "System",
            MessageRoleType.FUNCTION: "Function",
            MessageRoleType.TOOL: "Tool"
        }
        return display_names.get(self.value, self.value.value.title())
    
    def __str__(self) -> str:
        """String representation."""
        return self.value.value
    
    # Convenience class methods for common roles
    @classmethod
    def user(cls) -> 'MessageRole':
        """Create a user role."""
        return cls(MessageRoleType.USER)
    
    @classmethod
    def assistant(cls) -> 'MessageRole':
        """Create an assistant role."""
        return cls(MessageRoleType.ASSISTANT)
    
    @classmethod
    def system(cls) -> 'MessageRole':
        """Create a system role."""
        return cls(MessageRoleType.SYSTEM)