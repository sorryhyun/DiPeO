"""Domain rules for node connections in diagrams.

This module defines the business logic for which node types can connect to each other.
These are domain rules that govern the valid structure of diagrams.
"""

from dipeo.models import NodeType


class NodeConnectionRules:
    """Defines the rules for valid connections between node types."""
    
    @staticmethod
    def can_connect(source_type: NodeType, target_type: NodeType) -> bool:
        """Check if a connection from source to target node type is valid.
        
        Domain rules:
        - Start nodes cannot have inputs
        - Endpoint nodes cannot have outputs
        - All other connections follow specific type rules
        """
        # Start nodes cannot have any inputs
        if target_type == NodeType.start:
            return False
        
        # Endpoint nodes cannot have any outputs
        if source_type == NodeType.endpoint:
            return False
        
        # These node types can output to most others
        output_capable = {
            NodeType.person_job,
            NodeType.condition,
            NodeType.code_job,
            NodeType.api_job,
            NodeType.start
        }
        
        if source_type in output_capable:
            # Can connect to anything except start nodes
            return target_type != NodeType.start
        
        # Default: allow connection
        return True
    
    @staticmethod
    def get_connection_constraints(node_type: NodeType) -> dict[str, list[NodeType]]:
        """Get the connection constraints for a given node type.
        
        Returns:
            Dictionary with 'can_receive_from' and 'can_send_to' lists
        """
        all_types = list(NodeType)
        
        if node_type == NodeType.start:
            return {
                'can_receive_from': [],  # No inputs allowed
                'can_send_to': [t for t in all_types if t != NodeType.start]
            }
        
        if node_type == NodeType.endpoint:
            return {
                'can_receive_from': [t for t in all_types if t != NodeType.endpoint],
                'can_send_to': []  # No outputs allowed
            }
        
        # Most nodes can connect freely (except the constraints above)
        return {
            'can_receive_from': [t for t in all_types if t != NodeType.endpoint],
            'can_send_to': [t for t in all_types if t != NodeType.start]
        }