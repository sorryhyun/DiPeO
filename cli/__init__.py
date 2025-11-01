"""DiPeO Command-Line Interface.

This package provides the user-facing CLI tools for DiPeO:
- dipeo: Main CLI for running diagrams, compilation, and queries
- dipeocc: Claude Code session conversion tool

The CLI is a consumer of the dipeo core library, providing a
command-line interface for diagram operations, execution, and
management tasks.
"""

from .claude_code_manager import ClaudeCodeCommandManager
from .cli_runner import CLIRunner
from .diagram_loader import DiagramLoader
from .event_forwarder import EventForwarder
from .integration_manager import IntegrationCommandManager
from .interactive_handler import cli_interactive_handler
from .server_manager import ServerManager
from .session_manager import SessionManager

__version__ = "1.0.0"

__all__ = [
    "CLIRunner",
    "ClaudeCodeCommandManager",
    "DiagramLoader",
    "EventForwarder",
    "IntegrationCommandManager",
    "ServerManager",
    "SessionManager",
    "cli_interactive_handler",
]
