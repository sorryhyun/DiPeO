"""PersonJobNode handler - executes AI person jobs with conversation memory.

This package provides a complete implementation for executing PersonJob nodes,
supporting both single-person and batch execution modes.

Modules:
- handler: Main PersonJobNodeHandler class and service coordination
- single_executor: Single-person execution logic with template processing
- batch_executor: Batch execution logic with parallel/sequential processing
- batch_helpers: Batch processing utilities
- output_builder: Output formatting and representation building
- conversation_handler: Conversation operations and message handling
- text_format_handler: Structured output text format processing
- prompt_resolver: Prompt file resolution utilities
"""

from .handler import PersonJobNodeHandler

__all__ = ["PersonJobNodeHandler"]
