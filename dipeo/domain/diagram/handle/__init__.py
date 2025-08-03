"""Handle management utilities for DiPeO diagrams."""

from .handle_utils import (
    HandleReference,
    ParsedHandle,
    create_handle_id,
    extract_node_id_from_handle,
    is_valid_handle_id,
    parse_handle_id,
    parse_handle_id_safe,
)

__all__ = [
    'HandleReference',
    'ParsedHandle',
    'create_handle_id',
    'extract_node_id_from_handle',
    'is_valid_handle_id',
    'parse_handle_id',
    'parse_handle_id_safe',
]