"""Interactive handler for CLI user input."""

import asyncio
import sys
from typing import Any


async def cli_interactive_handler(event: dict[str, Any]) -> str:
    """Handle interactive user input via stdin.

    Args:
        event: Dict containing:
            - type: "user_input_required"
            - node_id: ID of requesting node
            - prompt: Question to display
            - timeout: Max wait time in seconds

    Returns:
        User's input string
    """
    prompt = event.get("prompt", "Enter input:")
    timeout = event.get("timeout", 60)
    node_id = event.get("node_id", "unknown")

    # Display prompt to user
    print(f"\n{'=' * 60}")
    print(f"🤔 User Input Required (Node: {node_id})")
    print(f"{'=' * 60}")
    print(f"\n{prompt}\n")
    print(f"⏱️  Timeout: {timeout} seconds")
    print(f"{'─' * 60}")
    print("Your response: ", end="", flush=True)

    # Read from stdin with timeout
    try:
        # Create async task for reading input
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(None, sys.stdin.readline), timeout=timeout
        )
        return response.strip()
    except asyncio.TimeoutError:
        print(f"\n⏰ Timeout after {timeout} seconds - using empty response")
        return ""
