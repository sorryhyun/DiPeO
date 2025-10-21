#!/usr/bin/env python3
"""
Add explicit anchors to markdown documentation headings.

Usage:
    python scripts/add_doc_anchors.py docs/features/mcp-server-integration.md --dry-run
    python scripts/add_doc_anchors.py docs/features/ --recursive
"""

import argparse
import re
from pathlib import Path


def slugify(text: str) -> str:
    """Convert heading text to GitHub-style anchor slug."""
    # Remove markdown links
    text = re.sub(r"\[([^\]]+)\]\([^\)]+\)", r"\1", text)
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and special chars with hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[-\s]+", "-", text)
    # Remove leading/trailing hyphens
    text = text.strip("-")
    return text


def has_explicit_anchor(line: str) -> bool:
    """Check if heading already has explicit anchor."""
    return bool(re.search(r"\{#[a-z0-9-]+\}", line))


def add_anchor_to_heading(line: str, prefix: str = "") -> str:
    """Add explicit anchor to a heading line if it doesn't have one."""
    # Skip if already has anchor
    if has_explicit_anchor(line):
        return line

    # Extract heading level and text
    match = re.match(r"^(#{1,6})\s+(.+?)(?:\s*\{#[^}]+\})?\s*$", line)
    if not match:
        return line

    level, text = match.groups()

    # Generate anchor
    anchor = slugify(text)
    if prefix:
        anchor = f"{prefix}-{anchor}"

    # Return heading with anchor
    return f"{level} {text} {{#{anchor}}}\n"


def process_file(
    filepath: Path, dry_run: bool = False, prefix: str = "", skip_h1: bool = True
) -> tuple[int, int]:
    """
    Add anchors to all headings in a markdown file.

    Returns:
        (headings_found, anchors_added)
    """
    content = filepath.read_text()
    lines = content.splitlines(keepends=True)

    headings_found = 0
    anchors_added = 0
    new_lines = []

    for line in lines:
        # Check if it's a heading
        if re.match(r"^#{1,6}\s+", line):
            headings_found += 1

            # Skip H1 headings if requested (usually page titles)
            if skip_h1 and line.startswith("# "):
                new_lines.append(line)
                continue

            # Check if already has anchor
            if has_explicit_anchor(line):
                new_lines.append(line)
                continue

            # Add anchor
            new_line = add_anchor_to_heading(line, prefix)
            new_lines.append(new_line)
            anchors_added += 1

            if dry_run:
                print(f"  Would add: {new_line.strip()}")
        else:
            new_lines.append(line)

    # Write back if not dry run
    if not dry_run and anchors_added > 0:
        filepath.write_text("".join(new_lines))
        print(f"✅ Updated {filepath}: {anchors_added}/{headings_found} anchors added")
    elif dry_run:
        print(f"📋 {filepath}: Would add {anchors_added}/{headings_found} anchors")
    else:
        print(f"✓ {filepath}: All {headings_found} headings already have anchors")

    return headings_found, anchors_added


def main():
    parser = argparse.ArgumentParser(
        description="Add explicit anchors to markdown documentation headings"
    )
    parser.add_argument("path", type=Path, help="File or directory to process")
    parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be changed without modifying files"
    )
    parser.add_argument("--recursive", action="store_true", help="Process directory recursively")
    parser.add_argument(
        "--prefix",
        default="",
        help="Add prefix to all anchors (e.g., 'mcp' for mcp-server-integration.md)",
    )
    parser.add_argument(
        "--include-h1", action="store_true", help="Add anchors to H1 headings (default: skip H1)"
    )

    args = parser.parse_args()

    if args.path.is_file():
        files = [args.path]
    elif args.path.is_dir():
        if args.recursive:
            files = sorted(args.path.rglob("*.md"))
        else:
            files = sorted(args.path.glob("*.md"))
    else:
        print(f"❌ Error: {args.path} not found")
        return 1

    # Filter out Korean translations
    files = [f for f in files if "korean" not in f.parts]

    print(f"Processing {len(files)} files...\n")

    total_headings = 0
    total_anchors = 0

    for filepath in files:
        headings, anchors = process_file(
            filepath, dry_run=args.dry_run, prefix=args.prefix, skip_h1=not args.include_h1
        )
        total_headings += headings
        total_anchors += anchors

    print(
        f"\n{'Would add' if args.dry_run else 'Added'} {total_anchors}/{total_headings} anchors across {len(files)} files"
    )

    return 0


if __name__ == "__main__":
    exit(main())
