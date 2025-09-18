"""Text processing utilities for Claude Code translation."""

from typing import Any


class TextProcessor:
    """Handles text extraction and processing for Claude Code sessions."""

    def __init__(self):
        """Initialize text processor."""
        self.last_tool_name = None

    def set_last_tool(self, tool_name: str | None) -> None:
        """Set the last tool name for context-aware processing."""
        self.last_tool_name = tool_name

    def extract_text_content(self, content: Any, skip_read_results: bool = False) -> str:
        """Extract text content from various content formats.

        Args:
            content: The content to extract text from
            skip_read_results: If True, skip tool_result content from Read operations
        """
        if isinstance(content, str):
            return content

        if isinstance(content, list):
            text_parts = []
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        text_parts.append(item.get("text", ""))
                    elif item.get("type") == "tool_result":
                        # Skip tool results for execution/operation tools when processing user input
                        tools_to_skip = {
                            "Read",
                            "Bash",
                            "Write",
                            "Edit",
                            "MultiEdit",
                            "Glob",
                            "Grep",
                        }
                        if skip_read_results and self.last_tool_name in tools_to_skip:
                            pass  # Skip these tool results in user input nodes
                        else:
                            # Include other tool results (like WebFetch, Task, etc.) in the content
                            result_content = item.get("content", "")
                            if result_content:
                                text_parts.append(result_content)
                    elif "content" in item:
                        text_parts.append(
                            self.extract_text_content(item["content"], skip_read_results)
                        )
                elif isinstance(item, str):
                    text_parts.append(item)
            return " ".join(text_parts)

        if isinstance(content, dict):
            if "text" in content:
                return str(content["text"])
            if "content" in content:
                return self.extract_text_content(content["content"], skip_read_results)

        return str(content)

    @staticmethod
    def unescape_string(s: str) -> str:
        """Unescape a string that may have been escaped in JSON/JSONL format.

        Handles common escape sequences:
        - \\" becomes "
        - \\n becomes newline
        - \\t becomes tab
        - \\\\ becomes \\
        """
        if not s:
            return s

        # Use Python's built-in decode for escape sequences
        # This handles standard JSON escape sequences
        try:
            # First try to decode as if it were a JSON string value
            # We need to wrap it in quotes for json.loads to work
            import json

            decoded = json.loads('"' + s + '"')
            return decoded
        except:
            # If that fails, just do basic replacements
            s = s.replace('\\"', '"')
            s = s.replace("\\n", "\n")
            s = s.replace("\\t", "\t")
            s = s.replace("\\\\", "\\")
            return s
