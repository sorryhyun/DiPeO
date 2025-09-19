"""Connection builder for Claude Code translation.

This module handles the creation and management of connections between
nodes in the DiPeO diagram during the conversion phase.
"""

from typing import Any


class ConnectionBuilder:
    """Builds connections between nodes in DiPeO diagrams."""

    def __init__(self):
        """Initialize the connection builder."""
        self.connections: list[dict[str, Any]] = []

    def reset(self):
        """Reset the connection builder state."""
        self.connections = []

    def add_connection(
        self, source: str, target: str, content_type: str = "raw_text", label: str = ""
    ) -> None:
        """Add a connection between two nodes in light format.

        Args:
            source: Source node label
            target: Target node label
            content_type: Type of content flowing through connection
            label: Optional connection label
        """
        connection = {"from": source, "to": target, "content_type": content_type}
        if label:
            connection["label"] = label
        self.connections.append(connection)

    def connect_sequential_nodes(self, node_labels: list[str]) -> None:
        """Connect a sequence of nodes in order.

        Args:
            node_labels: List of node labels to connect sequentially
        """
        for i in range(len(node_labels) - 1):
            self.add_connection(node_labels[i], node_labels[i + 1])

    def connect_to_previous(self, previous_node: str, current_nodes: list[str]) -> None:
        """Connect a previous node to the first of current nodes.

        Args:
            previous_node: Label of the previous node
            current_nodes: List of current node labels
        """
        if current_nodes and previous_node:
            self.add_connection(previous_node, current_nodes[0])

    def get_connections(self) -> list[dict[str, Any]]:
        """Get all connections built so far.

        Returns:
            List of connection dictionaries in light format
        """
        return self.connections.copy()
