#!/usr/bin/env python3
"""
Doc Lookup Section Search

Searches markdown documentation for specific sections by:
1. Explicit anchors (e.g., {#cli-flags})
2. Heading text fuzzy matching
3. Content keyword matching

Returns top matching sections with file path, heading, and content.
"""

import argparse
import re
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Section:
    """Represents a documentation section"""

    file_path: str
    heading: str
    level: int
    anchor: str | None
    content: str
    line_start: int


@dataclass
class ScoredSection:
    """Section with relevance score"""

    section: Section
    score: float
    match_type: str  # 'anchor', 'heading', 'content'


def slugify(text: str) -> str:
    """Convert heading text to anchor slug (GitHub-style)"""
    # Remove markdown formatting
    text = re.sub(r"[`*_\[\]]", "", text)
    # Convert to lowercase
    text = text.lower()
    # Replace spaces and special chars with hyphens
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    # Remove leading/trailing hyphens
    text = text.strip("-")
    return text


def extract_sections(file_path: Path) -> list[Section]:
    """Extract all sections from a markdown file"""
    sections = []

    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Warning: Could not read {file_path}: {e}")
        return sections

    lines = content.split("\n")
    current_section = None
    section_content = []

    for i, line in enumerate(lines, 1):
        # Match heading: ## Heading {#optional-anchor}
        heading_match = re.match(r"^(#{2,6})\s+(.+?)(?:\s*\{#([\w-]+)\})?$", line)

        if heading_match:
            # Save previous section
            if current_section is not None:
                current_section.content = "\n".join(section_content).strip()
                sections.append(current_section)

            # Start new section
            level = len(heading_match.group(1))
            heading_text = heading_match.group(2).strip()
            explicit_anchor = heading_match.group(3)

            # Use explicit anchor if present, otherwise slugify heading
            anchor = explicit_anchor if explicit_anchor else slugify(heading_text)

            current_section = Section(
                file_path=str(file_path),
                heading=heading_text,
                level=level,
                anchor=anchor,
                content="",
                line_start=i,
            )
            section_content = []
        elif current_section is not None:
            section_content.append(line)

    # Save last section
    if current_section is not None:
        current_section.content = "\n".join(section_content).strip()
        sections.append(current_section)

    return sections


def score_section(section: Section, query: str) -> ScoredSection | None:
    """Score a section's relevance to the query"""
    query_lower = query.lower()

    # 1. Exact anchor match (highest priority)
    if section.anchor and section.anchor.lower() == query_lower:
        return ScoredSection(section, 100.0, "anchor")

    # 2. Anchor contains query
    if section.anchor and query_lower in section.anchor.lower():
        return ScoredSection(section, 90.0, "anchor")

    # 3. Heading exact match
    if section.heading.lower() == query_lower:
        return ScoredSection(section, 80.0, "heading")

    # 4. Heading contains query
    if query_lower in section.heading.lower():
        # More specific = higher score
        ratio = len(query) / len(section.heading)
        score = 60.0 + (ratio * 20.0)
        return ScoredSection(section, score, "heading")

    # 5. Content keyword matching (simple scoring)
    query_words = set(query_lower.split())
    content_lower = section.content.lower()
    heading_lower = section.heading.lower()

    # Count keyword matches
    matches = sum(1 for word in query_words if word in content_lower or word in heading_lower)

    if matches > 0:
        # Score based on proportion of query words found
        score = (matches / len(query_words)) * 50.0
        return ScoredSection(section, score, "content")

    return None


def search_sections(paths: list[Path], query: str, top_n: int = 3) -> list[ScoredSection]:
    """Search for sections matching the query"""
    all_sections = []

    # Collect all sections from all files
    for path in paths:
        if path.is_file() and path.suffix in [".md", ".markdown"]:
            sections = extract_sections(path)
            all_sections.extend(sections)
        elif path.is_dir():
            # Recursively find markdown files
            for md_file in path.rglob("*.md"):
                sections = extract_sections(md_file)
                all_sections.extend(sections)

    # Score all sections
    scored_sections = []
    for section in all_sections:
        scored = score_section(section, query)
        if scored:
            scored_sections.append(scored)

    # Sort by score (descending) and return top N
    scored_sections.sort(key=lambda x: x.score, reverse=True)
    return scored_sections[:top_n]


def format_result(
    scored: ScoredSection, show_content: bool = True, max_content_lines: int = 30
) -> str:
    """Format a search result for display"""
    section = scored.section

    output = []
    output.append(f"\n{'='*80}")
    output.append(f"Score: {scored.score:.1f} (match type: {scored.match_type})")
    output.append(f"File: {section.file_path}:{section.line_start}")
    output.append(f"Heading: {'#' * section.level} {section.heading}")
    if section.anchor:
        output.append(f"Anchor: #{section.anchor}")

    if show_content:
        output.append(f"\n{'-'*80}")
        content_lines = section.content.split("\n")
        if len(content_lines) > max_content_lines:
            output.append("\n".join(content_lines[:max_content_lines]))
            output.append(f"\n... ({len(content_lines) - max_content_lines} more lines)")
        else:
            output.append(section.content)

    output.append(f"{'='*80}\n")
    return "\n".join(output)


def main():
    parser = argparse.ArgumentParser(
        description="Search markdown documentation for specific sections"
    )
    parser.add_argument(
        "--query", required=True, help="Search query (anchor ID, heading text, or keywords)"
    )
    parser.add_argument(
        "--paths", nargs="+", default=["docs/"], help="Paths to search (files or directories)"
    )
    parser.add_argument(
        "--top", type=int, default=3, help="Number of top results to return (default: 3)"
    )
    parser.add_argument(
        "--no-content", action="store_true", help="Show only headings without content"
    )
    parser.add_argument(
        "--max-lines",
        type=int,
        default=30,
        help="Maximum content lines to show per section (default: 30)",
    )

    args = parser.parse_args()

    # Convert string paths to Path objects
    paths = [Path(p) for p in args.paths]

    # Validate paths
    for path in paths:
        if not path.exists():
            print(f"Error: Path does not exist: {path}")
            return 1

    # Search
    results = search_sections(paths, args.query, args.top)

    # Display results
    if not results:
        print(f"\nNo sections found matching: {args.query}")
        print(f"Searched in: {', '.join(str(p) for p in paths)}")
        return 1

    print(f"\nFound {len(results)} matching section(s) for: {args.query}")
    print(f"Searched in: {', '.join(str(p) for p in paths)}")

    for result in results:
        print(format_result(result, not args.no_content, args.max_lines))

    return 0


if __name__ == "__main__":
    exit(main())
