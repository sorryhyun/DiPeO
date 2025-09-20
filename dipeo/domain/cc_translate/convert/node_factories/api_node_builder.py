"""API node builder for API call operations.

This module handles the creation of nodes for generic API calls and
web operations in DiPeO diagrams.
"""

from typing import Any, Optional

from .base_node_builder import BaseNodeBuilder


class ApiNodeBuilder(BaseNodeBuilder):
    """Builder for creating API call nodes."""

    def __init__(self, position_manager: Optional[Any] = None):
        """Initialize the API node builder.

        Args:
            position_manager: Optional position manager
        """
        super().__init__(position_manager)
        # These are tools that don't fit other categories
        self.supported_tools = [
            "WebFetch",
            "WebSearch",
            "Task",
            "ExitPlanMode",
            "BashOutput",
            "KillShell",
        ]

    def can_handle(self, tool_name: str) -> bool:
        """Check if this builder can handle the given tool.

        Args:
            tool_name: Name of the tool

        Returns:
            True if this builder handles API operations
        """
        # Handle known API tools or any unknown tools as generic API
        return tool_name in self.supported_tools or not self._is_known_tool(tool_name)

    def create_node(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Create an API call node.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters for the tool
            tool_result: Optional tool execution result

        Returns:
            The created node or None if not applicable
        """
        # Special handling for specific tools
        if tool_name == "WebFetch":
            return self.create_web_fetch_node(tool_input)
        elif tool_name == "WebSearch":
            return self.create_web_search_node(tool_input)
        elif tool_name == "Task":
            return self.create_task_node(tool_input)
        else:
            # Generic API node for unknown tools
            return self.create_generic_api_node(tool_name, tool_input)

    def create_web_fetch_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create an API node for web fetch operation.

        Args:
            tool_input: Input parameters including URL and prompt

        Returns:
            The created web fetch node
        """
        label = f"WebFetch {self.increment_counter()}"
        url = tool_input.get("url", "")
        prompt = tool_input.get("prompt", "")

        node = {
            "label": label,
            "type": "api_job",
            "position": self.get_position(),
            "props": {
                "endpoint": url,
                "method": "GET",
                "body": {"prompt": prompt},
                "timeout": 30,
                "description": "Fetch and process web content",
            },
        }
        self.nodes.append(node)
        return node

    def create_web_search_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create an API node for web search operation.

        Args:
            tool_input: Input parameters including query

        Returns:
            The created web search node
        """
        label = f"WebSearch {self.increment_counter()}"
        query = tool_input.get("query", "")
        allowed_domains = tool_input.get("allowed_domains", [])
        blocked_domains = tool_input.get("blocked_domains", [])

        node = {
            "label": label,
            "type": "api_job",
            "position": self.get_position(),
            "props": {
                "endpoint": "/search",
                "method": "POST",
                "body": {
                    "query": query,
                    "allowed_domains": allowed_domains,
                    "blocked_domains": blocked_domains,
                },
                "timeout": 30,
                "description": "Search the web",
            },
        }
        self.nodes.append(node)
        return node

    def create_task_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create an API node for Task (agent) invocation.

        Args:
            tool_input: Input parameters including subagent type and prompt

        Returns:
            The created task node
        """
        label = f"Task {self.increment_counter()}"
        subagent_type = tool_input.get("subagent_type", "general-purpose")
        prompt = tool_input.get("prompt", "")
        description = tool_input.get("description", "Launch agent")

        node = {
            "label": label,
            "type": "api_job",
            "position": self.get_position(),
            "props": {
                "endpoint": f"/agents/{subagent_type}",
                "method": "POST",
                "body": {"prompt": prompt, "description": description},
                "timeout": 600,  # Agents can take longer
                "description": f"Launch {subagent_type} agent",
            },
        }
        self.nodes.append(node)
        return node

    def create_generic_api_node(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a generic API node for unknown tools.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters

        Returns:
            The created generic API node
        """
        label = f"{tool_name} {self.increment_counter()}"

        node = {
            "label": label,
            "type": "api_job",
            "position": self.get_position(),
            "props": {
                "endpoint": f"/tools/{tool_name}",
                "method": "POST",
                "body": tool_input,
                "timeout": 30,
                "description": f"{tool_name} operation",
            },
        }
        self.nodes.append(node)
        return node

    def _is_known_tool(self, tool_name: str) -> bool:
        """Check if a tool is known to other builders.

        Args:
            tool_name: Name of the tool

        Returns:
            True if the tool is handled by another builder
        """
        known_tools = [
            # File operations
            "Read",
            "Write",
            "Edit",
            "MultiEdit",
            # Code operations
            "Bash",
            "Grep",
            "Glob",
            "Search",
            # Database operations
            "TodoWrite",
            "DatabaseQuery",
            "MemoryUpdate",
        ]
        return tool_name in known_tools
