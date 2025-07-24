"""
Constants used across the codegen modules.
"""

# Emoji to Lucide React icon name mapping
EMOJI_TO_ICON_MAP = {
    "🤖": "Bot",
    "🔧": "Wrench",
    "📝": "FileText",
    "🔀": "GitBranch",
    "🔄": "RefreshCw",
    "📊": "BarChart",
    "🚀": "Rocket",
    "⚡": "Zap",
    "📦": "Package",
    "🔑": "Key",
    "💾": "Save",
    "🌐": "Globe",
    "🔍": "Search",
    "⚙️": "Settings",
    "📨": "Send",
    "📥": "Download",
    "📤": "Upload",
    "🏁": "Flag",
    "🎯": "Target",
    "💡": "Lightbulb",
    "🔗": "Link",
    "🔒": "Lock",
    "🔓": "Unlock",
    "📁": "Folder",
    "📂": "FolderOpen",
}

def emoji_to_icon_name(emoji: str) -> str:
    """Convert emoji to Lucide React icon name."""
    return EMOJI_TO_ICON_MAP.get(emoji, "Activity")