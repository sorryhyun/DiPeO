"""Widget utilities for ChatGPT apps integration.

This module provides utilities for creating MCP responses with embedded widget resources
for ChatGPT apps to render rich UI components.
"""

import json
from pathlib import Path
from typing import Any, Dict

from dipeo.config.base_logger import get_module_logger
from mcp import types

logger = get_module_logger(__name__)

# Widget directory path
WIDGETS_DIR = Path(__file__).parent.parent.parent.parent / "static" / "widgets"


def load_widget_html(widget_name: str) -> str:
    """Load widget HTML from the static directory.

    Args:
        widget_name: Name of the widget (e.g., "execution-results")

    Returns:
        Widget HTML content

    Raises:
        FileNotFoundError: If widget file is not found
    """
    widget_files = list(WIDGETS_DIR.glob(f"{widget_name}-*.html"))

    if not widget_files:
        raise FileNotFoundError(f"Widget '{widget_name}' not found in {WIDGETS_DIR}")

    # Use the most recent file (highest hash)
    widget_file = sorted(widget_files)[-1]
    return widget_file.read_text()


def create_widget_response(
    widget_name: str,
    data: Dict[str, Any],
    text_summary: str | None = None,
) -> list[types.TextContent]:
    """Create an MCP response with embedded widget resource.

    Args:
        widget_name: Name of the widget to embed (e.g., "execution-results")
        data: Data to pass to the widget via setState
        text_summary: Optional text summary to display alongside the widget

    Returns:
        List of TextContent with widget metadata
    """
    try:
        widget_html = load_widget_html(widget_name)
        widget_file = list(WIDGETS_DIR.glob(f"{widget_name}-*.html"))[0]
        widget_uri = f"ui://widget/{widget_file.name}"

        widget_resource = types.EmbeddedResource(
            type="resource",
            resource=types.TextResourceContents(
                uri=widget_uri,
                mimeType="text/html+skybridge",
                text=widget_html,
            ),
        )

        return [
            types.TextContent(
                type="text",
                text=text_summary or json.dumps(data, indent=2),
                _meta={
                    "openai.com/widget": widget_resource.model_dump(),
                    "openai/outputTemplate": widget_uri,
                    "openai/widgetAccessible": True,
                },
            )
        ]

    except FileNotFoundError as e:
        logger.warning(f"Widget not found: {e}")
        # Fallback to plain text response
        return [
            types.TextContent(
                type="text",
                text=f"Widget '{widget_name}' not available. Data:\n{json.dumps(data, indent=2)}",
            )
        ]
    except Exception as e:
        logger.error(f"Error creating widget response: {e}")
        return [
            types.TextContent(
                type="text",
                text=f"Error loading widget: {str(e)}\nData:\n{json.dumps(data, indent=2)}",
            )
        ]


def is_widgets_available() -> bool:
    """Check if widgets directory exists and contains built widgets."""
    return WIDGETS_DIR.exists() and any(WIDGETS_DIR.glob("*.html"))
