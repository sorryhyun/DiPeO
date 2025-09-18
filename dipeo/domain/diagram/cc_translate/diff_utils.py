"""Diff generation utilities for Claude Code translation."""

import ast
import difflib
import json
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
    def parse_structured_patch_string(patch_str: str) -> Optional[list[dict[str, Any]]]:
        """Parse a string representation of a structured patch.

        Handles cases where structured patch is stored as a string
        (e.g., "[{'oldStart': 19, 'oldLines': 15, ...}]")

        Args:
            patch_str: String representation of structured patch

        Returns:
            Parsed list of hunk dictionaries, or None if not parseable
        """
        if not patch_str or not isinstance(patch_str, str):
            return None

        # Try to detect structured patch pattern
        if patch_str.strip().startswith("[{") and "oldStart" in patch_str:
            try:
                # First try ast.literal_eval (safer)
                parsed = ast.literal_eval(patch_str)
                if isinstance(parsed, list):
                    return parsed
            except (ValueError, SyntaxError):
                pass

            try:
                # Try JSON parsing
                parsed = json.loads(patch_str.replace("'", '"'))
                if isinstance(parsed, list):
                    return parsed
            except (ValueError, json.JSONDecodeError):
                pass

        return None

    @staticmethod
    def structured_to_unified(
        structured_patch: list[dict[str, Any]], file_path: str = "file"
    ) -> str:
        """Convert structured patch format to unified diff format.

        Structured patches from Claude Code contain hunks with:
        - oldStart: Starting line number in original file
        - oldLines: Number of lines from original file
        - newStart: Starting line number in new file
        - newLines: Number of lines in new file
        - lines: Array of line content with prefixes (' ', '+', '-')

        Args:
            structured_patch: List of hunk dictionaries
            file_path: File path for diff headers

        Returns:
            Unified diff format string
        """
        if not structured_patch:
            return f"# No changes in {file_path}"

        diff_lines = []

        # Add file headers
        diff_lines.append(f"--- {file_path}")
        diff_lines.append(f"+++ {file_path}")

        # Process each hunk
        for hunk in structured_patch:
            if not isinstance(hunk, dict):
                continue

            # Extract hunk metadata
            old_start = hunk.get("oldStart", 1)
            old_lines = hunk.get("oldLines", 0)
            new_start = hunk.get("newStart", 1)
            new_lines = hunk.get("newLines", 0)
            lines = hunk.get("lines", [])

            # Add hunk header
            diff_lines.append(f"@@ -{old_start},{old_lines} +{new_start},{new_lines} @@")

            # Add hunk lines
            for line in lines:
                # Lines should already have their prefixes
                # Just ensure we handle various formats
                if isinstance(line, str):
                    diff_lines.append(line)
                else:
                    diff_lines.append(str(line))

        return "\n".join(diff_lines)

    @staticmethod
    def accept_provider_patch_verbatim(patch_data: Any) -> str:
        """Accept provider patches verbatim with minimal processing.

        This method is designed for high-fidelity preservation of patches
        directly from Claude Code or other providers. It performs only
        essential normalization for YAML compatibility.

        Args:
            patch_data: Raw patch data from provider (string, list, or dict)

        Returns:
            Normalized patch string ready for YAML inclusion
        """
        if patch_data is None:
            return "# No patch data provided"

        # Convert structured data to string if needed
        if isinstance(patch_data, list | dict):
            # For structured patches, preserve the structure in a readable format
            if isinstance(patch_data, list):
                # Join list elements (common for multi-line patches)
                patch_str = "\n".join(str(item) for item in patch_data)
            else:
                # For dicts, convert to readable format
                try:
                    patch_str = json.dumps(patch_data, indent=2)
                except (TypeError, ValueError):
                    patch_str = str(patch_data)
        else:
            patch_str = str(patch_data)

        # Apply minimal normalization for YAML
        return DiffGenerator.normalize_diff_for_yaml(patch_str)

    @staticmethod
    def normalize_diff_for_yaml(diff_content: str) -> str:
        """Normalize diff strings for clean YAML literal blocks.

        This method ensures diffs are properly formatted for inclusion
        in YAML files as literal blocks:
        - Preserves line structure
        - Normalizes line endings to Unix-style (\n)
        - Ensures trailing newline for YAML compliance
        - Handles both string and structured patch formats
        """
        if not diff_content:
            return diff_content

        # Handle structured patches (may be JSON-like)
        if isinstance(diff_content, list | dict):
            import json

            try:
                diff_content = json.dumps(diff_content, indent=2)
            except (TypeError, ValueError):
                diff_content = str(diff_content)

        # Normalize line endings (CRLF -> LF)
        diff_content = diff_content.replace("\r\n", "\n").replace("\r", "\n")

        # Split and rejoin to ensure consistent formatting
        lines = diff_content.splitlines()
        normalized = "\n".join(lines)

        # Ensure trailing newline for YAML literal blocks
        if normalized and not normalized.endswith("\n"):
            normalized += "\n"

        return normalized
