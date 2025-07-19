"""Service for building node outputs."""

from typing import Any, List

from dipeo.core.dynamic import Person
from dipeo.core.execution.node_output import ConversationOutput, TextOutput, NodeOutputProtocol
from dipeo.core.static.generated_nodes import PersonJobNode
from dipeo.models import Message


class OutputBuilder:
    """Service for building node outputs based on node configuration and diagram connections."""
    
    def build_node_output(
        self, 
        result: Any, 
        person: Person, 
        node: PersonJobNode, 
        diagram: Any, 
        model: str
    ) -> NodeOutputProtocol:
        """Build appropriate output based on node and diagram configuration.
        
        Args:
            result: The completion result from the person
            person: The Person instance
            node: The PersonJobNode being executed
            diagram: The diagram containing node connections
            model: The LLM model used
            
        Returns:
            Either TextOutput or ConversationOutput based on connections
        """
        # Build metadata
        metadata = {"model": model}
        
        # Check if conversation output is needed
        if self._needs_conversation_output(str(node.id), diagram):
            # Return ConversationOutput with messages
            messages = []
            for msg in person.get_messages():
                messages.append(msg)
            
            return ConversationOutput(
                value=messages,
                node_id=node.id,
                metadata=metadata
            )
        else:
            # Return TextOutput with just the text
            return TextOutput(
                value=result.text,
                node_id=node.id,
                metadata=metadata
            )
    
    def _needs_conversation_output(self, node_id: str, diagram: Any) -> bool:
        """Check if any edge from this node expects conversation output.
        
        Args:
            node_id: The ID of the current node
            diagram: The diagram containing edges
            
        Returns:
            True if conversation output is needed
        """
        for edge in diagram.edges:
            if str(edge.source_node_id) == node_id:
                # Check for explicit conversation output
                if edge.source_output == "conversation":
                    return True
                # Check data_transform for content_type = conversation_state
                if hasattr(edge, 'data_transform') and edge.data_transform:
                    if edge.data_transform.get('content_type') == 'conversation_state':
                        return True
        return False