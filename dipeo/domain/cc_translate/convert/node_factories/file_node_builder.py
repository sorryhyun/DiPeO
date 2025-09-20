"""File node builder for file operations.

This module handles the creation of nodes for file operations including
read, write, and edit (diff_patch) operations in DiPeO diagrams.
"""

from typing import Any, Optional

from ..payload_processor import PayloadProcessor
from .base_node_builder import BaseNodeBuilder


class FileNodeBuilder(BaseNodeBuilder):
    """Builder for creating file operation nodes."""

    def __init__(
        self,
        payload_processor: Optional[PayloadProcessor] = None,
        position_manager: Optional[Any] = None,
    ):
        """Initialize the file node builder.

        Args:
            payload_processor: Processor for handling payloads
            position_manager: Optional position manager
        """
        super().__init__(position_manager)
        self.payload_processor = payload_processor or PayloadProcessor()
        self.supported_tools = ["Read", "Write", "Edit", "MultiEdit"]

    def can_handle(self, tool_name: str) -> bool:
        """Check if this builder can handle the given tool.

        Args:
            tool_name: Name of the tool

        Returns:
            True if this builder handles file operations
        """
        return tool_name in self.supported_tools

    def create_node(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Create a file operation node.

        Args:
            tool_name: Name of the tool
            tool_input: Input parameters for the tool
            tool_result: Optional tool execution result

        Returns:
            The created node or None if not applicable
        """
        if not self.can_handle(tool_name):
            return None

        if tool_name == "Read":
            return self.create_read_node(tool_input)
        elif tool_name == "Write":
            return self.create_write_node(tool_input, tool_result)
        elif tool_name in ["Edit", "MultiEdit"]:
            return self.create_edit_node(tool_name, tool_input, tool_result)

        return None

    def create_read_node(self, tool_input: dict[str, Any]) -> dict[str, Any]:
        """Create a DB node for file read operation.

        Args:
            tool_input: Input parameters including file path

        Returns:
            The created read node
        """
        label = f"Read File {self.increment_counter()}"
        file_path = tool_input.get("file_path", "unknown")

        node = {
            "label": label,
            "type": "db",
            "position": self.get_position(),
            "props": {
                "operation": "read",
                "sub_type": "file",
                "file": file_path,
            },
        }
        self.nodes.append(node)
        return node

    def create_write_node(
        self, tool_input: dict[str, Any], tool_result: Optional[dict[str, Any]] = None
    ) -> dict[str, Any]:
        """Create a DB node for file write operation.

        Args:
            tool_input: Input parameters including file path and content
            tool_result: Optional tool execution result

        Returns:
            The created write node
        """
        label = f"Write File {self.increment_counter()}"
        file_path = tool_input.get("file_path", "unknown")

        # Try to extract content from tool result first (more reliable)
        content = None
        if tool_result:
            payload = self.payload_processor.extract_tool_result_payload(tool_result)
            if payload:
                content = self.payload_processor.extract_file_content(payload)

        # Fall back to tool input if no result content
        if content is None:
            content = tool_input.get("content", "")

        node = {
            "label": label,
            "type": "db",
            "position": self.get_position(),
            "props": {
                "operation": "write",
                "sub_type": "file",
                "file": file_path,
                "content": content,
            },
        }
        self.nodes.append(node)
        return node

    def create_edit_node(
        self,
        tool_name: str,
        tool_input: dict[str, Any],
        tool_result: Optional[dict[str, Any]] = None,
    ) -> Optional[dict[str, Any]]:
        """Create a diff_patch node for file edit operation.

        Args:
            tool_name: Either "Edit" or "MultiEdit"
            tool_input: Input parameters including file path and changes
            tool_result: Optional tool execution result

        Returns:
            The created edit node or None if failed
        """
        label = f"{tool_name} File {self.increment_counter()}"
        file_path = tool_input.get("file_path", "unknown")

        # Extract payload and check for errors
        payload = self.payload_processor.extract_tool_result_payload(tool_result)
        if payload:
            is_error, error_msg = self.payload_processor.extract_error_info(payload)
            if is_error:
                print(f"Skipping failed {tool_name} for {file_path}: {error_msg}")
                return self._create_error_node(tool_name, file_path, error_msg)

        # Determine if we should create a diff_patch or write node
        if payload and self.payload_processor.should_create_diff_node(payload):
            return self._create_diff_patch_node(label, file_path, tool_name, tool_input, payload)
        elif payload and self.payload_processor.should_create_write_node(payload):
            # Full write without original - create db write node
            content = self.payload_processor.extract_file_content(payload)
            if content:
                return self._create_write_node_from_edit(file_path, content)

        # Fallback to simple diff from input
        return self._create_simple_diff_node(label, file_path, tool_name, tool_input)

    def _create_diff_patch_node(
        self,
        label: str,
        file_path: str,
        tool_name: str,
        tool_input: dict[str, Any],
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        """Create a diff_patch node with verified payload.

        Args:
            label: Node label
            file_path: Target file path
            tool_name: Tool name
            tool_input: Tool input parameters
            payload: Verified payload with diff content

        Returns:
            The created diff_patch node
        """
        # Import diff utilities
        from ..utils.diff_utils import DiffGenerator

        diff_generator = DiffGenerator()

        # Try to get patch directly from payload
        patch_data = payload.get("structuredPatch") or payload.get("patch")
        if patch_data:
            diff_content = diff_generator.accept_provider_patch_verbatim(patch_data)
        else:
            # Generate diff from tool result
            diff_content = diff_generator.generate_diff_from_tool_result(file_path, payload)

        if not diff_content:
            # Fallback to generating from input
            diff_content = self._generate_diff_from_input(file_path, tool_name, tool_input)

        node = {
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
        self.nodes.append(node)
        return node

    def _create_simple_diff_node(
        self, label: str, file_path: str, tool_name: str, tool_input: dict[str, Any]
    ) -> dict[str, Any]:
        """Create a simple diff_patch node from input only.

        Args:
            label: Node label
            file_path: Target file path
            tool_name: Tool name
            tool_input: Tool input parameters

        Returns:
            The created diff_patch node
        """
        diff_content = self._generate_diff_from_input(file_path, tool_name, tool_input)

        node = {
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
        self.nodes.append(node)
        return node

    def _create_write_node_from_edit(self, file_path: str, content: str) -> dict[str, Any]:
        """Create a write node when edit results in full file replacement.

        Args:
            file_path: Target file path
            content: Full file content

        Returns:
            The created write node
        """
        label = f"Write {file_path} {self.increment_counter()}"

        node = {
            "label": label,
            "type": "db",
            "position": self.get_position(),
            "props": {
                "operation": "write",
                "sub_type": "file",
                "file": file_path,
                "content": content,
            },
        }
        self.nodes.append(node)
        return node

    def _create_error_node(self, tool_name: str, file_path: str, error_msg: str) -> dict[str, Any]:
        """Create a TODO node for failed operations.

        Args:
            tool_name: Tool that failed
            file_path: Target file path
            error_msg: Error message

        Returns:
            A TODO node indicating the failure
        """
        label = f"Failed {tool_name} {self.increment_counter()}"

        node = {
            "label": label,
            "type": "db",
            "position": self.get_position(),
            "props": {
                "operation": "write",
                "sub_type": "memory",
                "query": "UPDATE TODO LIST",
                "data": {
                    "todos": [
                        {
                            "content": f"Failed {tool_name}: {error_msg}",
                            "status": "error",
                            "file": file_path,
                        }
                    ]
                },
            },
        }
        self.nodes.append(node)
        return node

    def _generate_diff_from_input(
        self, file_path: str, tool_name: str, tool_input: dict[str, Any]
    ) -> str:
        """Generate diff content from tool input.

        Args:
            file_path: Target file path
            tool_name: Tool name
            tool_input: Tool input parameters

        Returns:
            Generated diff content
        """
        # Import utilities
        from ..utils.diff_utils import DiffGenerator
        from ..utils.text_utils import TextProcessor

        diff_generator = DiffGenerator()
        text_processor = TextProcessor()

        if tool_name == "Edit":
            old_string = tool_input.get("old_string", "")
            new_string = tool_input.get("new_string", "")

            # Unescape strings for proper diff generation
            old_string = text_processor.unescape_string(old_string)
            new_string = text_processor.unescape_string(new_string)

            return diff_generator.generate_unified_diff(file_path, old_string, new_string)

        elif tool_name == "MultiEdit":
            edits = tool_input.get("edits", [])
            # Process edits to unescape strings
            processed_edits = []
            for edit in edits:
                if isinstance(edit, dict):
                    processed_edit = edit.copy()
                    if "old_string" in processed_edit:
                        processed_edit["old_string"] = text_processor.unescape_string(
                            processed_edit["old_string"]
                        )
                    if "new_string" in processed_edit:
                        processed_edit["new_string"] = text_processor.unescape_string(
                            processed_edit["new_string"]
                        )
                    processed_edits.append(processed_edit)

            return diff_generator.generate_multiedit_diff(file_path, processed_edits, None)

        return "# Unable to generate diff"
