"""Database node builder for database and memory operations.

This module handles the creation of nodes for database operations including
to-do list updates and other memory/database operations in DiPeO diagrams.
"""

from typing import Any, Optional

from .base_node_builder import BaseNodeBuilder


class DbNodeBuilder(BaseNodeBuilder):
    """Builder for creating database operation nodes."""

    def __init__(self, position_manager: Optional[Any] = None):
        """Initialize the database node builder.

        Args:
            position_manager: Optional position manager
        """
        super().__init__(position_manager)
        self.supported_tools = ["TodoWrite", "DatabaseQuery", "MemoryUpdate"]

    def can_handle(self, tool_name: str) -> bool:
        """Check if this builder can handle the given tool.

        Args:
            tool_name: Name of the tool

        Returns:
            True if this builder handles database operations
        """
        return tool_name in self.supported_tools

    def create_node(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Create a database operation node.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters for the tool
            tool_result: Optional tool execution result

        Returns:
            The created node or None if not applicable
        """
        if not self.can_handle(tool_name):
            return None

        if tool_name == "TodoWrite":
            return self.create_todo_node(tool_input)
        elif tool_name == "DatabaseQuery":
            return self.create_database_query_node(tool_input)
        elif tool_name == "MemoryUpdate":
            return self.create_memory_update_node(tool_input)

        return None

    def create_todo_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a DB node for TodoWrite operation.

        Args:
            tool_input: Input parameters including todos

        Returns:
            The created to-do node
        """
        label = f"Update TODO {self.increment_counter()}"
        todos = tool_input.get("todos", [])

        node = {
            "label": label,
            "type": "db",
            "position": self.get_position(),
            "props": {
                "operation": "write",
                "sub_type": "memory",
                "query": "UPDATE TODO LIST",
                "data": {"todos": todos},
            },
        }
        self.nodes.append(node)
        return node

    def create_database_query_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a DB node for database query operation.

        Args:
            tool_input: Input parameters including query

        Returns:
            The created database query node
        """
        label = f"Database Query {self.increment_counter()}"
        query = tool_input.get("query", "")
        database = tool_input.get("database", "default")

        node = {
            "label": label,
            "type": "db",
            "position": self.get_position(),
            "props": {
                "operation": "read",
                "sub_type": "database",
                "query": query,
                "database": database,
            },
        }
        self.nodes.append(node)
        return node

    def create_memory_update_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a DB node for memory update operation.

        Args:
            tool_input: Input parameters including memory data

        Returns:
            The created memory update node
        """
        label = f"Memory Update {self.increment_counter()}"
        memory_key = tool_input.get("key", "default")
        memory_value = tool_input.get("value", {})

        node = {
            "label": label,
            "type": "db",
            "position": self.get_position(),
            "props": {
                "operation": "write",
                "sub_type": "memory",
                "query": f"UPDATE MEMORY SET value = ? WHERE key = '{memory_key}'",
                "data": {"key": memory_key, "value": memory_value},
            },
        }
        self.nodes.append(node)
        return node
