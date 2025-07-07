"""Domain service for analyzing conversation structures and relationships."""

from typing import Optional, Any

from dipeo.models import (
    DomainDiagram,
    DomainPerson,
    ContentType,
    extract_node_id_from_handle,
)
from dipeo.core.utils import (
    is_conversation as core_is_conversation,
    has_nested_conversation as core_has_nested_conversation,
    contains_conversation as core_contains_conversation,
)


class ConversationAnalysisService:
    """Service for analyzing conversation structures in diagrams and inputs."""
    
    def find_person(
        self,
        diagram: Optional[DomainDiagram],
        person_id: str,
    ) -> Optional[DomainPerson]:
        """Find person in diagram."""
        if not diagram:
            return None
        return next((p for p in diagram.persons if p.id == person_id), None)
    
    def get_person_label(
        self,
        person_id: str,
        diagram: Optional[DomainDiagram],
    ) -> str:
        """Get the label for a person from the diagram."""
        if not diagram or not person_id:
            return person_id or "Person"
        
        person = self.find_person(diagram, person_id)
        return person.label if person else person_id
    
    def has_conversation_state_input(
        self,
        node_id: str,
        diagram: Optional[DomainDiagram],
        edges: Optional[list] = None,
    ) -> bool:
        """Check if this node has incoming conversation state.
        
        Business logic:
        - Examines diagram arrows to find incoming conversation connections
        - Checks content type to determine if conversation state is expected
        """
        if not diagram:
            return False
        
        # Check arrows for incoming conversation state
        for arrow in diagram.arrows:
            arrow_target_node_id = extract_node_id_from_handle(arrow.target)
            if (arrow_target_node_id == node_id and 
                arrow.content_type == ContentType.conversation_state):
                return True
        
        return False
    
    def needs_conversation_output(
        self,
        node_id: str,
        diagram: Optional[DomainDiagram],
    ) -> bool:
        """Check if any outgoing edge needs conversation data."""
        if not diagram:
            return False
            
        for arrow in diagram.arrows:
            # Check if arrow source belongs to this node
            arrow_source_node_id = extract_node_id_from_handle(arrow.source)
            if arrow_source_node_id == node_id and arrow.content_type == ContentType.conversation_state:
                return True
        return False
    
    def is_conversation(self, value: Any) -> bool:
        """Check if value is a conversation (list of messages)."""
        return core_is_conversation(value)
    
    def has_nested_conversation(self, inputs: dict[str, Any]) -> bool:
        """Check if inputs contain nested conversation structures.
        
        Business logic:
        - Checks for direct conversation values
        - Handles single-nested structures with 'default' key
        - Handles double-nested structures
        """
        for key, value in inputs.items():
            # Direct conversation
            if self.is_conversation(value):
                return True
                
            # Single-nested
            if isinstance(value, dict) and 'default' in value:
                nested = value['default']
                if self.is_conversation(nested):
                    return True
                
                # Double-nested
                if isinstance(nested, dict) and 'default' in nested:
                    double_nested = nested['default']
                    if self.is_conversation(double_nested):
                        return True
        
        return False
    
    def contains_conversation(self, inputs: dict[str, Any]) -> bool:
        """Check if the inputs contain any conversation data."""
        return core_contains_conversation(inputs)