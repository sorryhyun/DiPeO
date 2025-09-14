"""Styling constants and themes for the CLI display."""

from rich.style import Style
from rich.theme import Theme

# Color palette
COLORS = {
    "primary": "#00a8ff",
    "success": "#00ff88",
    "warning": "#ffaa00",
    "error": "#ff4444",
    "info": "#8888ff",
    "muted": "#666666",
    "highlight": "#ffff00",
    "background": "#1a1a1a",
    "foreground": "#ffffff",
}

# Status colors
STATUS_COLORS = {
    "PENDING": "white",
    "RUNNING": "yellow",
    "COMPLETED": "green",
    "FAILED": "red",
    "ABORTED": "red",
    "MAXITER_REACHED": "orange1",
    "SKIPPED": "grey50",
}

# Node type colors
NODE_TYPE_COLORS = {
    "START": "bright_blue",
    "PERSON_JOB": "cyan",
    "API_JOB": "magenta",
    "DB": "blue",
    "CODE_JOB": "yellow",
    "TEMPLATE_JOB": "green",
    "SUB_DIAGRAM": "purple",
    "CONDITION": "orange1",
    "HOOK": "dim cyan",
    "JSON_SCHEMA_VALIDATOR": "bright_magenta",
    "ENDPOINT": "bright_yellow",
    "USER_RESPONSE": "bright_green",
    "INTEGRATED_API": "bright_cyan",
}

# Icons
ICONS = {
    "success": "✓",
    "error": "✗",
    "warning": "⚠",
    "running": "⚡",
    "pending": "⏳",
    "info": "ℹ",
    "diagram": "📊",
    "node": "🔲",
    "time": "⏱️",
    "token": "🎫",
    "stats": "📈",
}

# Animation frames for spinners
SPINNER_FRAMES = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
PROGRESS_FRAMES = ["█", "▓", "▒", "░", " "]

# Create Rich theme
CLI_THEME = Theme(
    {
        "info": Style(color="#8888ff"),
        "warning": Style(color="#ffaa00"),
        "error": Style(color="#ff4444", bold=True),
        "success": Style(color="#00ff88", bold=True),
        "muted": Style(color="#666666", dim=True),
        "highlight": Style(color="#ffff00", bold=True),
        "title": Style(color="#00a8ff", bold=True),
        "subtitle": Style(color="#ffffff", italic=True),
        "progress.elapsed": Style(color="#8888ff"),
        "progress.remaining": Style(color="#666666"),
        "progress.percentage": Style(color="#00ff88"),
        "status.pending": Style(color="white", dim=True),
        "status.running": Style(color="yellow", bold=True),
        "status.completed": Style(color="green"),
        "status.failed": Style(color="red", bold=True),
    }
)
