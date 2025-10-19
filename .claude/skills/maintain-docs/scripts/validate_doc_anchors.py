#!/usr/bin/env python3
"""
Validate that all documentation anchors referenced in router skills exist.

Usage:
    python .claude/skills/maintain-docs/scripts/validate_doc_anchors.py
    python .claude/skills/maintain-docs/scripts/validate_doc_anchors.py .claude/skills/dipeo-backend/SKILL.md
"""

import argparse
import re
import sys
from pathlib import Path


def extract_doc_references(skill_file: Path) -> list[tuple[str, str]]:
    """
    Extract documentation references from a router skill.

    Returns:
        List of (file_path, anchor_id) tuples
    """
    content = skill_file.read_text()
    references = []

    # Match patterns like: docs/path/file.md#anchor-id
    pattern = r"(docs/[^\s\)]+\.md)#([a-z0-9-]+)"

    for match in re.finditer(pattern, content):
        filepath, anchor = match.groups()
        references.append((filepath, anchor))

    return references


def check_anchor_exists(filepath: str, anchor: str) -> bool:
    """Check if an anchor exists in a markdown file."""
    try:
        path = Path(filepath)
        if not path.exists():
            return False

        content = path.read_text()

        # Check for explicit anchor
        explicit_pattern = rf"\{{#{re.escape(anchor)}\}}"
        if re.search(explicit_pattern, content):
            return True

        # Check for auto-generated anchor (GitHub-style slug)
        # Convert anchor back to heading text possibilities
        # This is a heuristic check - may have false positives
        heading_text = anchor.replace("-", " ").title()
        heading_pattern = rf"^#+\s+.*{re.escape(heading_text)}.*$"
        if re.search(heading_pattern, content, re.MULTILINE | re.IGNORECASE):
            return True

        return False

    except Exception as e:
        print(f"Error checking {filepath}: {e}", file=sys.stderr)
        return False


def validate_skill(skill_file: Path) -> tuple[int, int, list[str]]:
    """
    Validate all doc references in a router skill.

    Returns:
        (total_refs, valid_refs, errors)
    """
    references = extract_doc_references(skill_file)
    errors = []

    for filepath, anchor in references:
        if not check_anchor_exists(filepath, anchor):
            errors.append(f"{skill_file.name}: {filepath}#{anchor} NOT FOUND")

    return len(references), len(references) - len(errors), errors


def main():
    parser = argparse.ArgumentParser(
        description="Validate documentation anchors referenced in router skills"
    )
    parser.add_argument(
        "skills",
        nargs="*",
        type=Path,
        help="Router skill files to validate (default: all in .claude/skills/)",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Exit with error code if any references are broken"
    )

    args = parser.parse_args()

    # Find skills to validate
    if args.skills:
        skill_files = args.skills
    else:
        # Find all SKILL.md files in .claude/skills/
        skills_dir = Path(".claude/skills")
        skill_files = sorted(skills_dir.glob("*/SKILL.md"))

    if not skill_files:
        print("No skill files found", file=sys.stderr)
        return 1

    print(f"Validating {len(skill_files)} router skills...\n")

    total_refs = 0
    total_valid = 0
    all_errors = []

    for skill_file in skill_files:
        refs, valid, errors = validate_skill(skill_file)
        total_refs += refs
        total_valid += valid
        all_errors.extend(errors)

        if refs > 0:
            status = "✅" if not errors else "⚠️"
            print(f"{status} {skill_file.parent.name}: {valid}/{refs} references valid")

    # Print errors
    if all_errors:
        print(f"\n❌ Found {len(all_errors)} broken references:\n")
        for error in all_errors:
            print(f"  {error}")
        print()

    # Summary
    print(f"\nSummary: {total_valid}/{total_refs} references valid ({len(all_errors)} broken)")

    if all_errors and args.strict:
        return 1

    return 0


if __name__ == "__main__":
    exit(main())
