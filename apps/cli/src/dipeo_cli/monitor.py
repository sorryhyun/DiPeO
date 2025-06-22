"""
Monitor command implementation for DiPeO CLI.
"""

import webbrowser
from typing import List


def monitor_command(args: List[str]) -> None:
    """Open browser monitoring page"""
    monitor_url = "http://localhost:3000/?monitor=true"
    print(f"🌐 Opening browser monitor at {monitor_url}")
    webbrowser.open(monitor_url)
