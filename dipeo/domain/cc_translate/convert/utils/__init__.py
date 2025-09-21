"""Utility modules for Claude Code to DiPeO conversion.

This module contains utility functions used during the conversion process
including text processing, diff generation, and payload classification.
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
    is_partial_diff,
    is_rich_diff,
    should_create_diff_node,
    should_create_write_node,
    validate_rich_diff_payload,
)
from .text_utils import TextProcessor

__all__ = [
    # Diff utilities
    "DiffGenerator",
    # Text utilities
    "TextProcessor",
    # Payload utilities
    "classify_payload",
    "extract_error_message",
    "extract_original_content",
    "extract_patch_data",
    "extract_write_content",
    "is_error_payload",
    "is_full_write",
    "is_partial_diff",
    "is_rich_diff",
    "should_create_diff_node",
    "should_create_write_node",
    "validate_rich_diff_payload",
]
