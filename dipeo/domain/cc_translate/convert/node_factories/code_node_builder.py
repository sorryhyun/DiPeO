"""Code node builder for code execution operations.

This module handles the creation of nodes for code execution including
bash commands and search operations in DiPeO diagrams.
"""

from typing import Any, Optional

from .base_node_builder import BaseNodeBuilder


class CodeNodeBuilder(BaseNodeBuilder):
    """Builder for creating code execution nodes."""

    def __init__(self, position_manager: Any | None = None):
        """Initialize the code node builder.

        Args:
            position_manager: Optional position manager
        """
        super().__init__(position_manager)
        self.supported_tools = ["Bash", "Grep", "Glob", "Search"]

    def can_handle(self, tool_name: str) -> bool:
        """Check if this builder can handle the given tool.

        Args:
            tool_name: Name of the tool

        Returns:
            True if this builder handles code execution operations
        """
        return tool_name in self.supported_tools

    def create_node(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: dict[str, Any] | None = None,
    ) -> dict[str, Any] | None:
        """Create a code execution node.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters for the tool
            tool_result: Optional tool execution result

        Returns:
            The created node or None if not applicable
        """
        if not self.can_handle(tool_name):
            return None

        if tool_name == "Bash":
            return self.create_bash_node(tool_input)
        elif tool_name in ["Grep", "Glob", "Search"]:
            return self.create_search_node(tool_name, tool_input)

        return None

    def create_bash_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a code_job node for bash command execution.

        Args:
            tool_input: Input parameters including command

        Returns:
            The created bash node
        """
        label = f"Bash Command {self.increment_counter()}"
        command = tool_input.get("command", "")
        description = tool_input.get("description", "Execute command")

        node = {
            "label": label,
            "type": "code_job",
            "position": self.get_position(),
            "props": {
                "language": "bash",
                "code": command,
                "timeout": tool_input.get("timeout", 120000),
                "description": description,
            },
        }
        self.nodes.append(node)
        return node

    def create_search_node(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a code_job node for search operations.

        Args:
            tool_name: Name of the search tool
            tool_input: Input parameters for the search

        Returns:
            The created search node
        """
        label = f"{tool_name} Search {self.increment_counter()}"

        if tool_name == "Grep":
            code = self._build_grep_command(tool_input)
        elif tool_name == "Glob":
            code = self._build_glob_command(tool_input)
        else:
            # Fallback for generic search
            query = tool_input.get("query", "") or tool_input.get("pattern", "")
            code = f"# {tool_name} search for: {query}"

        node = {
            "label": label,
            "type": "code_job",
            "position": self.get_position(),
            "props": {
                "language": "bash",
                "code": code,
                "tool": tool_name,
                "description": f"{tool_name} search operation",
            },
        }
        self.nodes.append(node)
        return node

    def _build_grep_command(self, tool_input: dict[str, Any]) -> str:
        """Build ripgrep command from Grep tool parameters.

        Args:
            tool_input: Grep tool input parameters

        Returns:
            The ripgrep command string
        """
        pattern = tool_input.get("pattern", "")
        path = tool_input.get("path", ".")

        # Start with base command
        cmd_parts = ["rg"]

        # Add flags
        if tool_input.get("-n"):
            cmd_parts.append("-n")
        if tool_input.get("-i"):
            cmd_parts.append("-i")
        if tool_input.get("-A"):
            cmd_parts.append(f"-A {tool_input['-A']}")
        if tool_input.get("-B"):
            cmd_parts.append(f"-B {tool_input['-B']}")
        if tool_input.get("-C"):
            cmd_parts.append(f"-C {tool_input['-C']}")
        if tool_input.get("multiline"):
            cmd_parts.append("-U --multiline-dotall")

        # Add type filter if specified
        if tool_input.get("type"):
            cmd_parts.append(f"--type {tool_input['type']}")

        # Add glob filter if specified
        if tool_input.get("glob"):
            cmd_parts.append(f"--glob '{tool_input['glob']}'")

        # Add output mode handling
        output_mode = tool_input.get("output_mode", "files_with_matches")
        if output_mode == "files_with_matches":
            cmd_parts.append("-l")
        elif output_mode == "count":
            cmd_parts.append("-c")
        # "content" is default, no flag needed

        # Add pattern (properly escaped)
        escaped_pattern = pattern.replace("'", "'\\''")
        cmd_parts.append(f"'{escaped_pattern}'")

        # Add path
        cmd_parts.append(path)

        # Add head limit if specified
        if tool_input.get("head_limit"):
            cmd_parts.append(f"| head -n {tool_input['head_limit']}")

        return " ".join(cmd_parts)

    def _build_glob_command(self, tool_input: dict[str, Any]) -> str:
        """Build find command from Glob tool parameters.

        Args:
            tool_input: Glob tool input parameters

        Returns:
            The find command string
        """
        pattern = tool_input.get("pattern", "")
        path = tool_input.get("path", ".")

        # Convert glob pattern to find command
        if "**" in pattern:
            # Recursive search
            name_pattern = pattern.replace("**/", "")
            code = f"find {path} -name '{name_pattern}' -type f"
        else:
            # Simple glob
            code = f"find {path} -maxdepth 1 -name '{pattern}' -type f"

        # Sort by modification time (newest first)
        code += " -printf '%T@ %p\\n' | sort -rn | cut -d' ' -f2-"

        return code
