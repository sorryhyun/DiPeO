"""Node builders for Claude Code translation to DiPeO diagrams."""

from typing import Any, Optional

from .diff_utils import DiffGenerator
from .text_utils import TextProcessor


class NodeBuilder:
    """Builds different types of nodes for DiPeO diagrams from Claude Code events."""

    def __init__(self):
        """Initialize the node builder."""
        self.node_counter = 0
        self.persons = {}
        self.text_processor = TextProcessor()
        self.diff_generator = DiffGenerator()

    def reset(self):
        """Reset the node builder state."""
        self.node_counter = 0
        self.persons = {}
        self.text_processor = TextProcessor()

    def increment_counter(self) -> int:
        """Increment and return the node counter."""
        self.node_counter += 1
        return self.node_counter

    def get_position(self) -> dict[str, int]:
        """Calculate node position based on current counter."""
        return {
            "x": 300 + (self.node_counter * 50) % 800,
            "y": 100 + (self.node_counter // 10) * 150,
        }

    def create_start_node(self, session_id: str, initial_prompt: str) -> dict[str, Any]:
        """Create the start node for the diagram."""
        return {
            "label": "Start",
            "type": "start",
            "position": {"x": 100, "y": 100},
            "props": {
                "trigger_mode": "manual",
                "custom_data": {
                    "session_id": session_id,
                    "initial_prompt": initial_prompt[:200]
                    if initial_prompt
                    else "Claude Code Session",
                },
            },
        }

    def create_user_node(self, content: str) -> dict[str, Any] | None:
        """Create a node for user input, or None if no meaningful input."""
        # Skip creating node if content is empty or just whitespace
        if not content or not content.strip():
            return None

        label = f"User Input {self.increment_counter()}"

        # Register user person if not exists
        if "user" not in self.persons:
            self.persons["user"] = {
                "service": "openai",
                "model": "user",
                "api_key_id": "USER_INPUT",
            }

        return {
            "label": label,
            "type": "person_job",
            "position": self.get_position(),
            "props": {
                "person": "user",
                "default_prompt": content,
                "max_iteration": 1,
            },
        }

    def create_assistant_node(self, content: str) -> dict[str, Any]:
        """Create a node for AI assistant response."""
        label = f"Claude Response {self.increment_counter()}"

        # Register Claude person if not exists
        if "claude_code" not in self.persons:
            self.persons["claude_code"] = {
                "service": "anthropic",
                "model": "claude-code",
                "api_key_id": "APIKEY_CLAUDE",
                "system_prompt": "You are Claude Code, an AI assistant helping with software development.",
            }

        return {
            "label": label,
            "type": "person_job",
            "position": self.get_position(),
            "props": {
                "person": "claude_code",
                "default_prompt": f"Process and respond: {content[:200]}",
                "max_iteration": 1,
            },
        }

    def create_read_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a DB node for file read operation."""
        label = f"Read File {self.increment_counter()}"
        file_path = tool_input.get("file_path", "unknown")

        return {
            "label": label,
            "type": "db",
            "position": self.get_position(),
            "props": {"operation": "read", "sub_type": "file", "file": file_path},
        }

    def create_write_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a DB node for file write operation."""
        label = f"Write File {self.increment_counter()}"
        file_path = tool_input.get("file_path", "unknown")
        content = tool_input.get("content", "")

        return {
            "label": label,
            "type": "db",
            "position": self.get_position(),
            "props": {
                "operation": "write",
                "sub_type": "file",
                "file": file_path,
                "content": content[:1000],  # Store some content for context
            },
        }

    def create_edit_node(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a diff_patch node for file edit operation."""
        label = f"{tool_name} File {self.increment_counter()}"
        file_path = tool_input.get("file_path", "unknown")

        # Generate unified diff from old_string and new_string
        if tool_name == "Edit":
            # Unescape strings that may have been escaped in the Claude Code session
            old_string = self.text_processor.unescape_string(tool_input.get("old_string", ""))
            new_string = self.text_processor.unescape_string(tool_input.get("new_string", ""))
            diff_content = self.diff_generator.generate_unified_diff(
                file_path, old_string, new_string
            )
        elif tool_name == "MultiEdit":
            # For MultiEdit, combine all edits into a single diff
            edits = tool_input.get("edits", [])
            # Unescape strings in each edit
            for edit in edits:
                if "old_string" in edit:
                    edit["old_string"] = self.text_processor.unescape_string(edit["old_string"])
                if "new_string" in edit:
                    edit["new_string"] = self.text_processor.unescape_string(edit["new_string"])
            diff_content = self.diff_generator.generate_multiedit_diff(file_path, edits)
        else:
            # Fallback for unknown edit types
            diff_content = "# Unable to generate diff"

        return {
            "label": label,
            "type": "diff_patch",
            "position": self.get_position(),
            "props": {
                "target_path": file_path,
                "diff": diff_content,
                "format": "unified",
                "backup": True,
                "validate": True,
            },
        }

    def create_bash_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a code_job node for bash command execution."""
        label = f"Bash Command {self.increment_counter()}"
        command = tool_input.get("command", "")
        description = tool_input.get("description", "Execute command")

        return {
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

    def create_todo_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a DB node for TodoWrite operation."""
        label = f"Update TODO {self.increment_counter()}"
        todos = tool_input.get("todos", [])

        return {
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

    def create_search_node(self, tool_name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a code_job node for search operations."""
        label = f"{tool_name} Search {self.increment_counter()}"

        if tool_name == "Grep":
            # Build ripgrep command from parameters
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

            code = " ".join(cmd_parts)

        elif tool_name == "Glob":
            # Build find command from glob pattern
            pattern = tool_input.get("pattern", "")
            path = tool_input.get("path", ".")

            # Convert glob pattern to find command
            # Common glob patterns: **/*.js, *.py, src/**/*.ts
            if "**" in pattern:
                # Recursive search
                name_pattern = pattern.replace("**/", "")
                code = f"find {path} -name '{name_pattern}' -type f"
            else:
                # Simple glob
                code = f"find {path} -maxdepth 1 -name '{pattern}' -type f"

            # Sort by modification time (newest first)
            code += " -printf '%T@ %p\\n' | sort -rn | cut -d' ' -f2-"

        else:
            # Fallback for unknown search tools
            query = tool_input.get("query", "") or tool_input.get("pattern", "")
            code = f"# {tool_name} search for: {query}"

        return {
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

    def create_generic_tool_node(
        self, tool_name: str, tool_input: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a generic API node for unknown tools."""
        label = f"{tool_name} {self.increment_counter()}"

        return {
            "label": label,
            "type": "api_job",
            "position": self.get_position(),
            "props": {
                "endpoint": f"/tools/{tool_name}",
                "method": "POST",
                "body": tool_input,
                "timeout": 30,
            },
        }

    def create_tool_node(
        self, tool_name: str, tool_input: dict[str, Any]
    ) -> Optional[dict[str, Any]]:
        """Create appropriate node based on tool name."""
        # Track the tool being used
        self.text_processor.set_last_tool(tool_name)

        if tool_name == "Read":
            return self.create_read_node(tool_input)
        elif tool_name == "Write":
            return self.create_write_node(tool_input)
        elif tool_name in ["Edit", "MultiEdit"]:
            return self.create_edit_node(tool_name, tool_input)
        elif tool_name == "Bash":
            return self.create_bash_node(tool_input)
        elif tool_name == "TodoWrite":
            return self.create_todo_node(tool_input)
        elif tool_name in ["Glob", "Grep"]:
            return self.create_search_node(tool_name, tool_input)
        else:
            # Generic API node for other tools
            return self.create_generic_tool_node(tool_name, tool_input)
