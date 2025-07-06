"""Service for aggregating and formatting conversations from multiple sources."""

import datetime
from typing import Any, Dict, List, Optional

from dipeo_core import BaseService
from dipeo_core.utils import is_conversation


class ConversationAggregationService(BaseService):
    """Handles aggregation and formatting of conversations from multiple person nodes."""
    
    async def initialize(self) -> None:
        """Initialize the service."""
        pass
    
    def aggregate_conversations(
        self, 
        inputs: Dict[str, Any], 
        diagram: Optional[Any] = None
    ) -> str:
        """Aggregate conversations from multiple sources into a formatted string.
        
        Args:
            inputs: Dictionary of inputs potentially containing conversations
            diagram: Optional diagram for getting person labels
            
        Returns:
            Formatted conversation string
        """
        # Collect all messages with timestamps
        all_messages = []
        
        for key, value in inputs.items():
            if is_conversation(value):
                self._extract_messages(value, all_messages)
            elif isinstance(value, dict):
                # Handle nested structures
                self._extract_nested_messages(value, all_messages)
        
        # Sort by timestamp
        all_messages.sort(key=lambda x: x.get('timestamp', 0))
        
        # Format as readable conversation flow
        return self._format_conversation(all_messages, diagram)
    
    
    def _extract_messages(self, messages: List[Dict[str, Any]], all_messages: List[Dict[str, Any]]) -> None:
        """Extract messages from a conversation list."""
        for msg in messages:
            # Get timestamp from message or use current time
            timestamp = msg.get('timestamp', datetime.datetime.now().timestamp())
            
            all_messages.append({
                'timestamp': timestamp,
                'person_id': msg.get('person_id', ''),
                'role': msg.get('role', ''),
                'content': msg.get('content', '')
            })
    
    def _extract_nested_messages(self, value: Dict[str, Any], all_messages: List[Dict[str, Any]]) -> None:
        """Extract messages from nested structures."""
        # Handle single-level nesting: {'default': [messages]}
        if 'default' in value and isinstance(value['default'], list):
            if is_conversation(value['default']):
                self._extract_messages(value['default'], all_messages)
            # Handle double-level nesting: {'default': {'default': [messages]}}
            elif isinstance(value['default'], dict) and 'default' in value['default']:
                nested = value['default']['default']
                if isinstance(nested, list) and is_conversation(nested):
                    self._extract_messages(nested, all_messages)
    
    def _format_conversation(self, messages: List[Dict[str, Any]], diagram: Optional[Any]) -> str:
        """Format messages as a readable conversation flow."""
        debate_text = []
        
        for msg in messages:
            if msg['role'] == 'user':
                # Check if it's already formatted with a label
                content = msg['content']
                if content.startswith('[') and ']:' in content:
                    # Already has a label (e.g., [Optimist]: or [developer]:)
                    debate_text.append(content)
                elif '[developer]:' in content:
                    # Has developer label somewhere in content
                    debate_text.append(content)
                else:
                    # Raw user message, add developer label
                    debate_text.append(f"[developer]: {content}")
            elif msg['role'] == 'assistant':
                # Format assistant responses with person labels
                person_label = self._get_person_label(msg['person_id'], diagram)
                debate_text.append(f"[{person_label}]: {msg['content']}")
        
        return '\n'.join(debate_text)
    
    def _get_person_label(self, person_id: str, diagram: Optional[Any]) -> str:
        """Get the label for a person from the diagram."""
        if not diagram or not person_id:
            return person_id or "Person"
            
        for person in getattr(diagram, "persons", []):
            if person.id == person_id:
                return person.label or person_id
                
        return person_id
    
    def detect_nested_conversation(self, inputs: Dict[str, Any]) -> bool:
        """Detect if inputs contain nested conversation structures."""
        for key, value in inputs.items():
            # Check for direct conversation
            if is_conversation(value):
                return True
                
            # Check for nested structures
            if isinstance(value, dict) and 'default' in value:
                nested = value['default']
                if is_conversation(nested):
                    return True
                # Check double nesting
                if isinstance(nested, dict) and 'default' in nested:
                    if isinstance(nested['default'], list) and is_conversation(nested['default']):
                        return True
        
        return False