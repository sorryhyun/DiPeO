#!/usr/bin/env python3
"""
Generate an index of all documentation anchors for easy reference.

Usage:
    python scripts/generate_anchor_index.py > docs/ANCHOR_INDEX.md
    python scripts/generate_anchor_index.py --json > .claude/data/anchors.json
"""

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path


def extract_anchors(filepath: Path) -> list[tuple[str, str, str]]:
    """
    Extract all anchors from a markdown file.

    Returns:
        List of (heading_level, heading_text, anchor_id)
    """
    content = filepath.read_text()
    anchors = []

    for line in content.splitlines():
        # Match headings with explicit anchors
        match = re.match(r"^(#{1,6})\s+(.+?)\s+\{#([a-z0-9-]+)\}\s*$", line)
        if match:
            level, text, anchor = match.groups()
            anchors.append((level, text, anchor))

    return anchors


def generate_markdown_index(anchor_map: dict[str, list[tuple[str, str, str]]]) -> str:
    """Generate markdown anchor index."""
    lines = [
        "# DiPeO Documentation Anchor Index",
        "",
        "Auto-generated index of all documentation anchors for use with doc-lookup skill.",
        "",
        "**Usage**: Reference anchors in router skills or use with doc-lookup:",
        "```bash",
        "python .claude/skills/doc-lookup/scripts/section_search.py \\",
        '  --query "anchor-id" \\',
        "  --paths docs/path/to/file.md \\",
        "  --top 1",
        "```",
        "",
        "---",
        "",
    ]

    # Group by category
    categories = {
        "docs/agents/": "## Agent Documentation",
        "docs/architecture/": "## Architecture",
        "docs/features/": "## Features",
        "docs/formats/": "## Formats",
        "docs/projects/": "## Projects",
    }

    for prefix, title in categories.items():
        # Get files in this category
        category_files = {k: v for k, v in anchor_map.items() if k.startswith(prefix)}

        if not category_files:
            continue

        lines.append(title)
        lines.append("")

        for filepath in sorted(category_files.keys()):
            anchors = category_files[filepath]
            if not anchors:
                continue

            # File header
            lines.append(f"### {filepath}")
            lines.append("")

            # Group anchors by level
            for level, text, anchor in anchors:
                indent = "  " * (len(level) - 2)  # Indent based on heading level
                lines.append(f"{indent}- `#{anchor}` - {text}")

            lines.append("")

    return "\n".join(lines)


def generate_json_index(anchor_map: dict[str, list[tuple[str, str, str]]]) -> str:
    """Generate JSON anchor index for programmatic use."""
    result = {}

    for filepath, anchors in anchor_map.items():
        result[filepath] = [
            {"level": len(level), "text": text, "anchor": anchor} for level, text, anchor in anchors
        ]

    return json.dumps(result, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Generate index of all documentation anchors")
    parser.add_argument("--json", action="store_true", help="Output as JSON instead of Markdown")
    parser.add_argument(
        "--docs-dir",
        type=Path,
        default=Path("docs"),
        help="Documentation directory (default: docs/)",
    )

    args = parser.parse_args()

    # Find all markdown files (exclude Korean translations)
    md_files = [f for f in args.docs_dir.rglob("*.md") if "korean" not in f.parts]

    # Extract anchors
    anchor_map = {}
    total_anchors = 0

    for filepath in sorted(md_files):
        rel_path = str(filepath)
        anchors = extract_anchors(filepath)
        if anchors:
            anchor_map[rel_path] = anchors
            total_anchors += len(anchors)

    # Generate output
    if args.json:
        output = generate_json_index(anchor_map)
    else:
        output = generate_markdown_index(anchor_map)

    print(output)

    # Print stats to stderr
    import sys

    print(f"\n✅ Found {total_anchors} anchors across {len(anchor_map)} files", file=sys.stderr)

    return 0


if __name__ == "__main__":
    exit(main())
