"""Shared utilities for MCP implementations.

This module contains common logic shared between the legacy MCP server
and the new MCP SDK-based implementation.
"""

import json
import logging
import os
from dataclasses import dataclass
from typing import Any, Optional

from dipeo.config.base_logger import get_module_logger
from dipeo_server.app_context import get_container
from dipeo_server.cli import CLIRunner

logger = get_module_logger(__name__)

DEFAULT_MCP_TIMEOUT = int(os.environ.get("MCP_DEFAULT_TIMEOUT", "300"))
DEBUG_MODE = os.environ.get("DIPEO_DEBUG", "false").lower() == "true"


@dataclass
class DiagramExecutionResult:
    """Result of a diagram execution."""

    success: bool
    diagram: str
    format_type: str
    error: Optional[str] = None

    def to_json(self, indent: int = 2) -> str:
        data = {
            "success": self.success,
            "diagram": self.diagram,
            "format": self.format_type,
        }

        if self.success:
            data["message"] = "Diagram executed successfully"
        else:
            data["message"] = "Diagram execution failed"
            if self.error:
                data["error"] = self.error

        return json.dumps(data, indent=indent)


class DiagramExecutionError(Exception):
    pass


async def execute_diagram_shared(
    diagram: Optional[str],
    input_data: Optional[dict[str, Any]] = None,
    format_type: str = "light",
    timeout: int = DEFAULT_MCP_TIMEOUT,
    validate_inputs: bool = True,
) -> DiagramExecutionResult:
    """Execute a DiPeO diagram with shared logic between MCP implementations."""
    if not diagram:
        raise DiagramExecutionError("diagram parameter is required")

    if validate_inputs and input_data is not None and not isinstance(input_data, dict):
        raise DiagramExecutionError("input_data must be a dictionary")

    if validate_inputs:
        valid_formats = ["light", "native", "readable"]
        if format_type not in valid_formats:
            raise DiagramExecutionError(
                f"Invalid format_type: {format_type}. Must be one of {valid_formats}"
            )

    try:
        logger.info(f"Executing diagram via MCP: {diagram}")

        container = get_container()
        cli = CLIRunner(container)

        success = await cli.run_diagram(
            diagram=diagram,
            debug=False,
            timeout=timeout,
            format_type=format_type,
            input_variables=input_data if input_data else None,
            use_unified=True,
            simple=True,
            interactive=False,
        )

        return DiagramExecutionResult(
            success=success,
            diagram=diagram,
            format_type=format_type,
        )

    except Exception as e:
        logger.error(f"Error executing diagram via MCP: {e}", exc_info=True)

        error_msg = str(e) if DEBUG_MODE else "Diagram execution failed"

        return DiagramExecutionResult(
            success=False,
            diagram=diagram,
            format_type=format_type,
            error=error_msg,
        )
