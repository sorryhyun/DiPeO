import re
from typing import Any


def validate_diff(diff_content: str, format_type: str) -> list[str]:
    """Validate the diff content for basic structure.

    Args:
        diff_content: The diff content to validate
        format_type: The format of the diff (unified, git, context)

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    if not diff_content.strip():
        errors.append("Diff content is empty")
        return errors

    if format_type == "unified" or format_type == "git":
        if not re.search(r"^---\s+", diff_content, re.MULTILINE):
            errors.append("Missing '---' header for original file")
        if not re.search(r"^\+\+\+\s+", diff_content, re.MULTILINE):
            errors.append("Missing '+++' header for new file")
        if not re.search(r"^@@\s+-\d+", diff_content, re.MULTILINE):
            errors.append("Missing hunk headers (@@)")
    elif format_type == "context":
        if not re.search(r"^\*\*\*\s+", diff_content, re.MULTILINE):
            errors.append("Missing '***' header for original file")
        if not re.search(r"^---\s+", diff_content, re.MULTILINE):
            errors.append("Missing '---' header for new file")

    return errors


def parse_hunks(diff_content: str) -> list[dict[str, Any]]:
    """Parse diff content into hunks.

    Args:
        diff_content: The diff content to parse

    Returns:
        List of hunk dictionaries with old_start, old_lines, new_start, new_lines, and lines
    """
    hunks = []
    current_hunk = None

    for line in diff_content.splitlines():
        if line.startswith("@@"):
            match = re.match(r"^@@\s+-(\d+)(?:,(\d+))?\s+\+(\d+)(?:,(\d+))?\s+@@", line)
            if match:
                current_hunk = {
                    "old_start": int(match.group(1)),
                    "old_lines": int(match.group(2) or 1),
                    "new_start": int(match.group(3)),
                    "new_lines": int(match.group(4) or 1),
                    "lines": [],
                }
                hunks.append(current_hunk)
        elif current_hunk:
            current_hunk["lines"].append(line)

    return hunks


def reverse_diff(diff_content: str, format_type: str) -> str:
    """Reverse a diff (swap additions and deletions).

    Args:
        diff_content: The diff content to reverse
        format_type: The format of the diff (currently unused)

    Returns:
        Reversed diff content
    """
    reversed_lines = []

    for line in diff_content.splitlines():
        if line.startswith("---"):
            reversed_lines.append(
                line.replace("---", "+++temp").replace("+++", "---").replace("+++temp", "+++")
            )
        elif line.startswith("+++"):
            reversed_lines.append(
                line.replace("+++", "---temp").replace("---", "+++").replace("---temp", "---")
            )
        elif line.startswith("-"):
            reversed_lines.append("+" + line[1:])
        elif line.startswith("+"):
            reversed_lines.append("-" + line[1:])
        else:
            reversed_lines.append(line)

    return "\n".join(reversed_lines)
