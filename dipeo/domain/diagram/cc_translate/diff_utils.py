"""Diff generation utilities for Claude Code translation."""

import difflib
from typing import Any, Optional


class DiffGenerator:
    """Generates unified diffs for file edit operations.

    This class supports two modes of diff generation:
    1. High-fidelity: When original file content is available from tool_use_result
    2. Snippet-based: Fallback mode using only old_string and new_string

    All diffs are normalized for clean YAML output with literal blocks.
    """

    @staticmethod
    def generate_unified_diff(file_path: str, old_content: str, new_content: str) -> str:
        """Generate a unified diff from old and new content strings."""
        # Split content into lines for difflib (without keeping line endings)
        old_lines = old_content.splitlines()
        new_lines = new_content.splitlines()

        # Generate unified diff
        diff_lines = list(
            difflib.unified_diff(
                old_lines,
                new_lines,
                fromfile=file_path,
                tofile=file_path,
                n=3,  # Context lines
                lineterm="",  # Don't add line terminators
            )
        )

        # Join the diff lines with newlines
        if diff_lines:
            # Join with real newlines - no normalization needed here
            return "\n".join(diff_lines)
        else:
            # No differences found
            return f"# No differences found in {file_path}"

    @staticmethod
    def apply_edits_to_content(original_content: str, edits: list[dict[str, Any]]) -> str:
        """Apply a series of edits to original content."""
        current_content = original_content

        for edit in edits:
            old_string = edit.get("old_string", "")
            new_string = edit.get("new_string", "")
            replace_all = edit.get("replace_all", False)

            if old_string in current_content:
                if replace_all:
                    current_content = current_content.replace(old_string, new_string)
                else:
                    # Replace only the first occurrence
                    current_content = current_content.replace(old_string, new_string, 1)
            # If old_string not found, continue with next edit (defensive)

        return current_content

    @staticmethod
    def generate_multiedit_diff(
        file_path: str, edits: list[dict[str, Any]], original_content: Optional[str] = None
    ) -> str:
        """Generate a unified diff from multiple edit operations."""
        if not edits:
            return f"# No edits provided for {file_path}"

        # If we have original content, apply edits and generate a single unified diff
        if original_content:
            modified_content = DiffGenerator.apply_edits_to_content(original_content, edits)
            return DiffGenerator.generate_unified_diff(
                file_path, original_content, modified_content
            )

        # Fallback: generate individual diffs and combine
        diff_sections = []
        diff_sections.append(f"# MultiEdit diff for {file_path}")
        diff_sections.append(f"# Total edits: {len(edits)}")
        diff_sections.append("")

        for i, edit in enumerate(edits, 1):
            old_string = edit.get("old_string", "")
            new_string = edit.get("new_string", "")

            diff_sections.append(f"# Edit {i}/{len(edits)}")

            # Generate diff for this specific edit
            edit_diff = DiffGenerator.generate_unified_diff(file_path, old_string, new_string)
            diff_sections.append(edit_diff)
            diff_sections.append("")  # Add blank line between edits

        return "\n".join(diff_sections)

    @staticmethod
    def generate_diff_from_tool_result(
        file_path: str, tool_result: dict[str, Any]
    ) -> Optional[str]:
        """Generate a diff using the rich tool result payload."""
        # Direct diff strings from providers take priority when present
        structured_patch = (
            tool_result.get("structuredPatch")
            or tool_result.get("patch")
            or tool_result.get("diff")
        )
        if structured_patch:
            return DiffGenerator.normalize_diff_for_yaml(str(structured_patch))

        # Extract data from tool result
        original_file = tool_result.get("originalFile") or tool_result.get("originalFileContents")
        old_string = tool_result.get("oldString")
        new_string = tool_result.get("newString")

        # If we have the complete original file and the edit strings, generate full diff
        if original_file and old_string is not None and new_string is not None:
            # Apply the edit to the original content
            modified_content = original_file.replace(old_string, new_string, 1)
            return DiffGenerator.generate_unified_diff(file_path, original_file, modified_content)

        # Fallback to snippet-based diff if we have old and new strings
        if old_string is not None and new_string is not None:
            return DiffGenerator.generate_unified_diff(file_path, old_string, new_string)

        # No useful data for diff generation
        return None

    @staticmethod
    def normalize_diff_for_yaml(diff_content: str) -> str:
        """Normalize diff strings for clean YAML literal blocks."""
        if not diff_content:
            return diff_content

        lines = diff_content.splitlines()
        normalized = "\n".join(lines)
        if not normalized.endswith("\n"):
            normalized += "\n"
        return normalized
