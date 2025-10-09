"""Payload processing for tool results in Claude Code translation.

This module handles the extraction and processing of tool result payloads
to determine the appropriate node creation strategy.
"""

from typing import Any, Optional


class PayloadProcessor:
    """Processes tool result payloads for node creation decisions."""

    def extract_tool_result_payload(
        self, tool_use_result: dict[str, Any] | list[Any] | str | None
    ) -> dict[str, Any] | None:
        """Select the most useful tool result payload for diff generation.

        Args:
            tool_use_result: The tool use result from Claude Code

        Returns:
            The most useful payload dictionary or None
        """
        if not tool_use_result:
            return None

        candidates: list[Any]
        if isinstance(tool_use_result, dict):
            candidates = [tool_use_result]
        elif isinstance(tool_use_result, list):
            # Prefer latest results (reverse order)
            candidates = [item for item in reversed(tool_use_result)]
        else:
            # Strings or other primitives are not useful for diff reconstruction
            return None

        for candidate in candidates:
            if not isinstance(candidate, dict):
                continue

            # Ignore explicit errors or empty payloads
            if candidate.get("error") or candidate.get("status") == "error":
                continue

            # Check for useful content
            has_content = any(
                key in candidate
                for key in (
                    "structuredPatch",
                    "patch",
                    "diff",
                    "originalFile",
                    "originalFileContents",
                    "content",
                    "result",
                )
            )
            if not has_content:
                continue

            return candidate

        return None

    def extract_file_content(
        self, payload: dict[str, Any], key_priority: list[str] | None = None
    ) -> str | None:
        """Extract file content from a payload.

        Args:
            payload: The payload dictionary
            key_priority: Priority list of keys to check (default: common content keys)

        Returns:
            The extracted content or None
        """
        if not payload:
            return None

        # Default priority for content keys
        if key_priority is None:
            key_priority = [
                "content",
                "file_content",
                "fileContent",
                "data",
                "text",
                "body",
            ]

        for key in key_priority:
            if key in payload:
                content = payload[key]
                if isinstance(content, str):
                    return content
                elif isinstance(content, dict) and "text" in content:
                    return content["text"]

        return None

    def extract_error_info(self, payload: dict[str, Any]) -> tuple[bool, str | None]:
        """Extract error information from a payload.

        Args:
            payload: The payload dictionary

        Returns:
            Tuple of (is_error, error_message)
        """
        if not payload:
            return False, None

        # Check for explicit error fields
        if payload.get("error"):
            error_msg = payload.get("error")
            if isinstance(error_msg, str):
                return True, error_msg
            elif isinstance(error_msg, dict):
                return True, error_msg.get("message", str(error_msg))
            return True, str(error_msg)

        if payload.get("status") == "error":
            return True, payload.get("message", "Unknown error")

        if payload.get("success") is False:
            return True, payload.get("message", "Operation failed")

        return False, None

    def extract_file_path(self, payload: dict[str, Any]) -> str | None:
        """Extract file path from a payload.

        Args:
            payload: The payload dictionary

        Returns:
            The extracted file path or None
        """
        if not payload:
            return None

        # Check common file path keys
        path_keys = ["file_path", "filePath", "path", "file", "target", "filename"]

        for key in path_keys:
            if key in payload:
                path = payload[key]
                if isinstance(path, str):
                    return path

        return None

    def extract_operation_type(self, payload: dict[str, Any]) -> str | None:
        """Determine the operation type from a payload.

        Args:
            payload: The payload dictionary

        Returns:
            The operation type (e.g., "read", "write", "edit") or None
        """
        if not payload:
            return None

        # Check explicit operation field
        if "operation" in payload:
            return payload["operation"]

        # Infer from content structure
        if any(
            key in payload
            for key in ["structuredPatch", "patch", "diff", "old_string", "new_string"]
        ):
            return "edit"

        if any(key in payload for key in ["content", "file_content", "write_content", "data"]):
            # Check if it's a read based on other indicators
            if payload.get("mode") == "r" or payload.get("action") == "read":
                return "read"
            return "write"

        if any(key in payload for key in ["command", "code", "script"]):
            return "execute"

        if any(key in payload for key in ["query", "search", "pattern"]):
            return "search"

        return None

    def should_create_diff_node(self, payload: dict[str, Any]) -> bool:
        """Determine if a diff_patch node should be created.

        Args:
            payload: The payload dictionary

        Returns:
            True if a diff_patch node should be created
        """
        if not payload:
            return False

        # Check for error
        is_error, _ = self.extract_error_info(payload)
        if is_error:
            return False

        # Check for diff/patch content
        return any(
            key in payload
            for key in [
                "structuredPatch",
                "patch",
                "diff",
                "originalFile",
                "originalFileContents",
            ]
        )

    def should_create_write_node(self, payload: dict[str, Any]) -> bool:
        """Determine if a write node should be created.

        Args:
            payload: The payload dictionary

        Returns:
            True if a write node should be created
        """
        if not payload:
            return False

        # Check for error
        is_error, _ = self.extract_error_info(payload)
        if is_error:
            return False

        # Must have content but no original/diff info
        has_content = any(key in payload for key in ["content", "file_content", "write_content"])

        has_diff_info = any(
            key in payload
            for key in [
                "structuredPatch",
                "patch",
                "diff",
                "originalFile",
                "originalFileContents",
            ]
        )

        return has_content and not has_diff_info

    def merge_payloads(self, primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
        """Merge two payloads, with primary taking precedence.

        Args:
            primary: Primary payload (takes precedence)
            secondary: Secondary payload

        Returns:
            Merged payload dictionary
        """
        merged = secondary.copy()
        merged.update(primary)
        return merged
