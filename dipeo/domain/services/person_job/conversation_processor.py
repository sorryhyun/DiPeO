"""Domain service for processing conversation inputs and state."""

from typing import Any, Dict, List, Optional, Set

from dipeo.models import (
    DomainDiagram,
    DomainPerson,
    DomainArrow,
)


class ConversationProcessingService:
    """Service for handling conversation processing business logic."""
    
    def consolidate_on_every_turn_messages(
        self,
        inputs: Dict[str, Any],
        used_keys: Set[str],
        diagram: DomainDiagram,
    ) -> str:
        """Consolidate conversation messages for on_every_turn mode.
        
        Business logic:
        - Detects and consolidates conversation states from inputs
        - Formats messages with person labels when available
        - Handles external message inputs
        - Preserves tool outputs
        """
        consolidated = []
        
        # Process conversation states
        for key, value in inputs.items():
            if key not in used_keys and self._is_conversation_state(value):
                person_label = self._find_person_label_for_key(key, diagram)
                messages = self._format_conversation_messages(value, person_label)
                consolidated.extend(messages)
                used_keys.add(key)
        
        # Process external messages
        if "external_messages" in inputs and "external_messages" not in used_keys:
            external = inputs["external_messages"]
            if isinstance(external, list):
                for msg in external:
                    if isinstance(msg, dict) and "content" in msg:
                        formatted_msg = self._format_external_message(msg)
                        consolidated.append(formatted_msg)
                used_keys.add("external_messages")
        
        return "\n\n".join(consolidated)
    
    def has_conversation_state_input(
        self,
        inputs: Dict[str, Any],
        diagram: DomainDiagram,
    ) -> bool:
        """Check if any input contains conversation state."""
        for value in inputs.values():
            if self._is_conversation_state(value):
                return True
        return False
    
    def needs_conversation_output(
        self,
        node_id: str,
        diagram: DomainDiagram,
    ) -> bool:
        """Determine if node needs conversation output based on connections."""
        # Check if any outgoing edge is marked for conversation
        for arrow in diagram.arrows or []:
            # Check if arrow source starts from this node
            # TODO: Need to parse source HandleID to extract node_id properly
            if arrow.source and str(arrow.source).startswith(node_id):
                return True
        return False
    
    def find_person(
        self,
        diagram: DomainDiagram,
        person_id: str,
    ) -> Optional[DomainPerson]:
        """Find a person in the diagram by ID."""
        if not diagram.persons:
            return None
            
        for person in diagram.persons:
            if person.id == person_id:
                return person
        return None
    
    def get_person_label(
        self,
        person_id: str,
        diagram: DomainDiagram,
    ) -> str:
        """Get the display label for a person."""
        person = self.find_person(diagram, person_id)
        if person and person.label:
            return person.label
        return person_id
    
    def format_conversation_for_output(
        self,
        messages: List[Dict[str, Any]],
        person_label: str,
    ) -> Dict[str, Any]:
        """Format messages into a conversation state for output."""
        # Return a dictionary that represents the conversation state
        # instead of using the Conversation model which has different requirements
        return {
            "messages": messages,  # messages are already in dict format
            "person": person_label,
            "metadata": None
        }
    
    def _is_conversation_state(self, value: Any) -> bool:
        """Check if a value represents a conversation state."""
        if not isinstance(value, dict):
            return False
            
        # Check for conversation state structure
        if "messages" in value and isinstance(value.get("messages"), list):
            return True
            
        # Check for single message structure
        if "role" in value and "content" in value:
            return True
            
        return False
    
    def _find_person_label_for_key(
        self,
        key: str,
        diagram: DomainDiagram,
    ) -> Optional[str]:
        """Find the person label associated with an input key."""
        # Look for connections that might provide context
        for arrow in diagram.arrows or []:
            # Check if arrow involves this key
            # TODO: Need to parse HandleIDs to check slot names properly
            if arrow.source == key or arrow.target == key:
                # Try to find the person from the source node
                # Extract node_id from source HandleID (format: node_id_slot_type)
                source_parts = str(arrow.source).split('_')
                if source_parts:
                    node_id = source_parts[0]
                    node = self._find_node_by_id(node_id, diagram)
                if node and hasattr(node, "person_id"):
                    return self.get_person_label(node.person_id, diagram)
        return None
    
    def _find_node_by_id(self, node_id: str, diagram: DomainDiagram) -> Optional[Any]:
        """Find a node by ID in the diagram."""
        for node in diagram.nodes or []:
            if node.id == node_id:
                return node
        return None
    
    def _format_conversation_messages(
        self,
        conversation: Dict[str, Any],
        person_label: Optional[str],
    ) -> List[str]:
        """Format conversation messages for display."""
        formatted = []
        
        messages = conversation.get("messages", [])
        for msg in messages:
            if isinstance(msg, dict):
                content = msg.get("content", "")
                role = msg.get("role", "")
                
                if person_label:
                    formatted.append(f"[{person_label} - {role}]: {content}")
                else:
                    formatted.append(f"[{role}]: {content}")
        
        return formatted
    
    def _format_external_message(self, msg: Dict[str, Any]) -> str:
        """Format an external message."""
        content = msg.get("content", "")
        role = msg.get("role", "user")
        return f"[{role}]: {content}"