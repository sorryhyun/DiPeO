"""Utility methods for conversation handling."""

from typing import Optional, Any
from dipeo_domain.models import DomainDiagram, DomainPerson, ContentType
from dipeo_core import RuntimeContext


class ConversationUtils:
    """Utility methods for conversation and person handling."""
    
    @staticmethod
    def find_person(diagram: Optional[DomainDiagram], person_id: str) -> Optional[DomainPerson]:
        """Find person in diagram."""
        if not diagram:
            return None
        return next((p for p in diagram.persons if p.id == person_id), None)
    
    @staticmethod
    def get_person_label(person_id: str, diagram: Optional[DomainDiagram]) -> str:
        """Get the label for a person from the diagram."""
        if not diagram or not person_id:
            return person_id or "Person"
        
        person = ConversationUtils.find_person(diagram, person_id)
        return person.label if person else person_id
    
    @staticmethod
    def has_conversation_state_input(
        context: RuntimeContext, 
        diagram: Optional[DomainDiagram]
    ) -> bool:
        """Check if this node has incoming conversation state."""
        if not diagram:
            return False
        
        for edge in context.edges:
            if edge.get("target", "").startswith(context.current_node_id):
                source_node_id = ConversationUtils._extract_node_id_from_handle(
                    edge.get("source", "")
                )
                
                for arrow in diagram.arrows:
                    if (arrow.source.startswith(source_node_id) and 
                        arrow.target.startswith(context.current_node_id) and
                        arrow.content_type == ContentType.conversation_state):
                        return True
        return False
    
    @staticmethod
    def needs_conversation_output(
        node_id: str, 
        diagram: Optional[DomainDiagram]
    ) -> bool:
        """Check if any outgoing edge needs conversation data."""
        if not diagram:
            return False
            
        for arrow in diagram.arrows:
            # Check if arrow source belongs to this node
            source_parts = arrow.source.split("_")
            if len(source_parts) >= 3:
                arrow_source_node_id = "_".join(source_parts[:-2])
                if arrow_source_node_id == node_id and arrow.content_type == ContentType.conversation_state:
                    return True
        return False
    
    @staticmethod
    def _extract_node_id_from_handle(handle: str) -> str:
        """Extract node ID from handle format: nodeId_handleName_direction."""
        if not handle:
            return ""
        parts = handle.split("_")
        return "_".join(parts[:-2]) if len(parts) >= 3 else handle


class InputDetector:
    """Simplified input detection utilities."""
    
    @staticmethod
    def is_conversation(value: Any) -> bool:
        """Check if value is a conversation (list of messages)."""
        return (isinstance(value, list) and 
                value and 
                all(isinstance(item, dict) and 
                    "role" in item and 
                    "content" in item for item in value))
    
    @staticmethod
    def has_nested_conversation(inputs: dict[str, Any]) -> bool:
        """Check if inputs contain nested conversation structures."""
        for key, value in inputs.items():
            # Direct conversation
            if InputDetector.is_conversation(value):
                return True
                
            # Single-nested
            if isinstance(value, dict) and 'default' in value:
                nested = value['default']
                if InputDetector.is_conversation(nested):
                    return True
                
                # Double-nested
                if isinstance(nested, dict) and 'default' in nested:
                    double_nested = nested['default']
                    if InputDetector.is_conversation(double_nested):
                        return True
        
        return False
    
    @staticmethod
    def contains_conversation(inputs: dict[str, Any]) -> bool:
        """Check if the inputs contain any conversation data."""
        for key, value in inputs.items():
            if InputDetector.is_conversation(value):
                return True
        return False


class MessageBuilder:
    """Builder pattern for cleaner message handling."""
    
    def __init__(self, conversation_service: Any, person_id: str, execution_id: str):
        self.service = conversation_service
        self.person_id = person_id
        self.execution_id = execution_id
    
    def add(self, role: str, content: str) -> 'MessageBuilder':
        """Add a message and return self for chaining."""
        self.service.add_message_to_conversation(
            person_id=self.person_id,
            execution_id=self.execution_id,
            role=role,
            content=content,
            current_person_id=self.person_id
        )
        return self
    
    def user(self, content: str) -> 'MessageBuilder':
        """Add user message."""
        return self.add("user", content)
    
    def assistant(self, content: str) -> 'MessageBuilder':
        """Add assistant message."""
        return self.add("assistant", content)
    
    def external(self, key: str, value: str) -> 'MessageBuilder':
        """Add external input message."""
        return self.add("external", f"[Input from {key}]: {value}")
    
    def developer(self, prompt: str) -> 'MessageBuilder':
        """Add developer prompt."""
        return self.add("user", f"[developer]: {prompt}")