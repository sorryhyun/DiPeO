"""Business logic for valid node type connections in diagrams."""

from dipeo.diagram_generated import NodeType


class NodeConnectionRules:
    @staticmethod
    def can_connect(source_type: NodeType, target_type: NodeType) -> bool:
        """Start nodes cannot have inputs, endpoint nodes cannot have outputs."""
        if target_type == NodeType.START:
            return False

        if source_type == NodeType.ENDPOINT:
            return False

        output_capable = {
            NodeType.PERSON_JOB,
            NodeType.CONDITION,
            NodeType.CODE_JOB,
            NodeType.API_JOB,
            NodeType.START,
        }

        if source_type in output_capable:
            return target_type != NodeType.START

        return True

    @staticmethod
    def get_connection_constraints(node_type: NodeType) -> dict[str, list[NodeType]]:
        """Returns 'can_receive_from' and 'can_send_to' lists."""
        all_types = list(NodeType)

        if node_type == NodeType.START:
            return {
                "can_receive_from": [],
                "can_send_to": [t for t in all_types if t != NodeType.START],
            }

        if node_type == NodeType.ENDPOINT:
            return {
                "can_receive_from": [t for t in all_types if t != NodeType.ENDPOINT],
                "can_send_to": [],
            }

        return {
            "can_receive_from": [t for t in all_types if t != NodeType.ENDPOINT],
            "can_send_to": [t for t in all_types if t != NodeType.START],
        }
