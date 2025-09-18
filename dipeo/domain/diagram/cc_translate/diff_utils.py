"""Diff generation utilities for Claude Code translation."""

import difflib
from typing import Any


class DiffGenerator:
    """Generates unified diffs for file edit operations."""

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
            return "\n".join(diff_lines)
        else:
            # No differences found
            return f"# No differences found in {file_path}"

    @staticmethod
    def generate_multiedit_diff(file_path: str, edits: list[dict[str, Any]]) -> str:
        """Generate a unified diff from multiple edit operations."""
        if not edits:
            return f"# No edits provided for {file_path}"

        # For MultiEdit, we need to apply edits sequentially
        # Since we don't have the original file content, we'll create individual diffs
        # and combine them with comments

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
