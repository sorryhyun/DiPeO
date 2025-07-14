# Conversation handling utilities

from typing import TYPE_CHECKING, Any

from dipeo.core.utils import contains_conversation as core_contains_conversation
from dipeo.core.utils import is_conversation as core_is_conversation
from dipeo.models import Message, PersonID

if TYPE_CHECKING:
    from dipeo.core.dynamic.conversation_manager import ConversationManager


class InputDetector:
    
    @staticmethod
    def is_conversation(value: Any) -> bool:
        return core_is_conversation(value)
    
    @staticmethod
    def has_nested_conversation(inputs: dict[str, Any]) -> bool:
        for key, value in inputs.items():
            if InputDetector.is_conversation(value):
                return True
                
            if isinstance(value, dict) and 'default' in value:
                nested = value['default']
                if InputDetector.is_conversation(nested):
                    return True
                
                if isinstance(nested, dict) and 'default' in nested:
                    double_nested = nested['default']
                    if InputDetector.is_conversation(double_nested):
                        return True
        
        return False
    
    @staticmethod
    def contains_conversation(inputs: dict[str, Any]) -> bool:
        return core_contains_conversation(inputs)


class MessageBuilder:
    
    def __init__(self, conversation_service: "ConversationManager", person_id: str, execution_id: str):
        self.service = conversation_service
        self.person_id = person_id
        self.execution_id = execution_id
    
    def add(self, role: str, content: str) -> 'MessageBuilder':
        # Create message based on role
        if role == "system":
            from_person_id = "system"
            to_person_id = PersonID(self.person_id)
            message_type = "system_to_person"
        elif role == "assistant":
            from_person_id = PersonID(self.person_id)
            to_person_id = "system"  # Assistant messages typically go to system
            message_type = "person_to_system"
        elif role == "user":
            from_person_id = "system"  # User messages come from system context
            to_person_id = PersonID(self.person_id)
            message_type = "system_to_person"
        else:  # external or other
            from_person_id = "system"
            to_person_id = PersonID(self.person_id)
            message_type = "system_to_person"
        
        message = Message(
            from_person_id=from_person_id,
            to_person_id=to_person_id,
            content=content,
            message_type=message_type,  # type: ignore
            metadata={"role": role}
        )
        
        self.service.add_message(
            message=message,
            execution_id=self.execution_id
        )
        return self
    
    def user(self, content: str) -> 'MessageBuilder':
        return self.add("user", content)
    
    def assistant(self, content: str) -> 'MessageBuilder':
        return self.add("assistant", content)
    
    def external(self, key: str, value: str) -> 'MessageBuilder':
        return self.add("external", f"[Input from {key}]: {value}")
    
    def developer(self, prompt: str) -> 'MessageBuilder':
        return self.add("user", f"[developer]: {prompt}")