"""Payload classification utilities for Claude Code tool results.

This module provides utilities for classifying and validating tool result payloads
from Claude Code sessions. It identifies which payloads contain sufficient information
for high-fidelity diff generation versus those that require fallback handling.
"""

from typing import Any, Optional, TypedDict, TypeGuard


class RichDiffPayload(TypedDict, total=False):
    """Structure of a payload that contains rich diff information."""

    # Original content (at least one of these)
    originalFile: str
    originalFileContents: str

    # Patch data (at least one of these)
    structuredPatch: Any  # Can be string or structured data
    patch: str
    diff: str

    # Edit details
    oldString: str
    newString: str

    # Metadata
    status: str
    error: str


class FullWritePayload(TypedDict, total=False):
    """Structure of a payload that contains full write content."""

    content: str
    newFile: str
    fileContents: str
    status: str


def is_error_payload(payload: Any) -> bool:
    """Check if a payload represents an error/failure.

    Args:
        payload: The tool result payload to check

    Returns:
        True if the payload indicates an error/failure
    """
    # String payloads starting with "Error:" are failures
    if isinstance(payload, str):
        return payload.strip().startswith("Error:") or "not found" in payload.lower()

    # Dict payloads with error field or error status
    if isinstance(payload, dict):
        if payload.get("error"):
            return True
        if payload.get("status") == "error":
            return True
        # Check for error messages in string content
        content = payload.get("content", "")
        if isinstance(content, str) and content.strip().startswith("Error:"):
            return True

    return False


def is_rich_diff(payload: Any) -> TypeGuard[RichDiffPayload]:
    """Check if a payload contains rich diff information.

    A rich diff payload contains both original file content and patch data,
    allowing for high-fidelity diff generation.

    Args:
        payload: The tool result payload to check

    Returns:
        True if the payload contains sufficient data for rich diff generation
    """
    if not isinstance(payload, dict):
        return False

    # Skip error payloads
    if is_error_payload(payload):
        return False

    # Must have original content
    has_original = bool(payload.get("originalFile") or payload.get("originalFileContents"))

    # Must have patch data
    has_patch = bool(payload.get("structuredPatch") or payload.get("patch") or payload.get("diff"))

    return has_original and has_patch


def is_partial_diff(payload: Any) -> bool:
    """Check if a payload contains partial diff information.

    A partial diff has edit strings but no full original content,
    suitable for snippet-based diff generation.

    Args:
        payload: The tool result payload to check

    Returns:
        True if the payload contains partial diff data
    """
    if not isinstance(payload, dict):
        return False

    # Skip error payloads
    if is_error_payload(payload):
        return False

    # Has old/new strings but not necessarily full content
    has_strings = payload.get("oldString") is not None and payload.get("newString") is not None

    # Not a rich diff (lacks full context or patch)
    return has_strings and not is_rich_diff(payload)


def is_full_write(payload: Any) -> TypeGuard[FullWritePayload]:
    """Check if a payload contains full write content.

    A full write payload contains complete file content but no original state,
    suitable for creating write nodes rather than diff nodes.

    Args:
        payload: The tool result payload to check

    Returns:
        True if the payload represents a full write operation
    """
    if not isinstance(payload, dict):
        return False

    # Skip error payloads
    if is_error_payload(payload):
        return False

    # Has new content but no original
    has_content = bool(
        payload.get("content") or payload.get("newFile") or payload.get("fileContents")
    )

    # No original file reference
    has_no_original = not bool(payload.get("originalFile") or payload.get("originalFileContents"))

    return has_content and has_no_original


def extract_patch_data(payload: dict[str, Any]) -> str | None:
    """Extract patch/diff data from a payload.

    Args:
        payload: The payload to extract from

    Returns:
        The patch data as a string, or None if not found
    """
    # Try different patch field names in priority order
    patch = payload.get("structuredPatch") or payload.get("patch") or payload.get("diff")

    if patch:
        # Convert to string if needed
        if isinstance(patch, str):
            return patch
        elif isinstance(patch, list):
            # Join list elements for structured patches
            return "\n".join(str(item) for item in patch)
        else:
            return str(patch)

    return None


def extract_original_content(payload: dict[str, Any]) -> str | None:
    """Extract original file content from a payload.

    Args:
        payload: The payload to extract from

    Returns:
        The original file content, or None if not found
    """
    return payload.get("originalFile") or payload.get("originalFileContents")


def extract_write_content(payload: dict[str, Any]) -> str | None:
    """Extract write content from a payload.

    Args:
        payload: The payload to extract from

    Returns:
        The content to write, or None if not found
    """
    return payload.get("content") or payload.get("newFile") or payload.get("fileContents")


def classify_payload(payload: Any) -> str:
    """Classify a tool result payload by type.

    Args:
        payload: The payload to classify

    Returns:
        One of: "error", "rich_diff", "partial_diff", "full_write", "unknown"
    """
    if is_error_payload(payload):
        return "error"
    elif is_rich_diff(payload):
        return "rich_diff"
    elif is_partial_diff(payload):
        return "partial_diff"
    elif is_full_write(payload):
        return "full_write"
    else:
        return "unknown"


def should_create_diff_node(payload: Any) -> bool:
    """Determine if a payload should result in a diff_patch node.

    Only rich diffs with verified content should become diff nodes.
    Errors and writes should not.

    Args:
        payload: The payload to check

    Returns:
        True if a diff_patch node should be created
    """
    return is_rich_diff(payload)


def should_create_write_node(payload: Any) -> bool:
    """Determine if a payload should result in a write node.

    Full writes without original content should become write nodes.

    Args:
        payload: The payload to check

    Returns:
        True if a write node should be created
    """
    return is_full_write(payload)


def extract_error_message(payload: Any) -> str | None:
    """Extract error message from a failure payload.

    Args:
        payload: The payload to extract from

    Returns:
        The error message, or None if not an error
    """
    if isinstance(payload, str):
        if payload.strip().startswith("Error:"):
            return payload.strip()
    elif isinstance(payload, dict):
        if payload.get("error"):
            return str(payload["error"])
        content = payload.get("content", "")
        if isinstance(content, str) and content.strip().startswith("Error:"):
            return content.strip()

    return None


def validate_rich_diff_payload(payload: dict[str, Any]) -> tuple[bool, str | None]:
    """Validate that a rich diff payload has all required fields.

    Args:
        payload: The payload to validate

    Returns:
        A tuple of (is_valid, error_message)
    """
    if not is_rich_diff(payload):
        return False, "Payload is not a rich diff"

    original = extract_original_content(payload)
    if not original:
        return False, "Missing original file content"

    patch = extract_patch_data(payload)
    if not patch:
        return False, "Missing patch data"

    return True, None
