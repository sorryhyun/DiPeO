"""Shared utilities for Claude Code translation.

Common utilities used across all phases including:
- Text processing and unescaping
- Payload classification and validation
- Diff generation utilities
- Common data structures and types
"""

from .diff_utils import DiffGenerator
from .payload_utils import (
    classify_payload,
    extract_error_message,
    extract_original_content,
    extract_patch_data,
    extract_write_content,
    is_error_payload,
    is_full_write,
    is_rich_diff,
    should_create_diff_node,
    should_create_write_node,
)
from .text_utils import TextProcessor

__all__ = [
    "DiffGenerator",
    "TextProcessor",
    "classify_payload",
    "extract_error_message",
    "extract_original_content",
    "extract_patch_data",
    "extract_write_content",
    "is_error_payload",
    "is_full_write",
    "is_rich_diff",
    "should_create_diff_node",
    "should_create_write_node",
]
