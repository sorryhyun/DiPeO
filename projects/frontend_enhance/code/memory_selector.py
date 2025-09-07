"""
Memory selector helper for intelligent context selection in frontend generation.
Uses section dependencies and keywords to build memorize_to criteria.
"""

def build_memorize_criteria(section, all_sections, include_keywords=True):
    """
    Build memorize_to criteria based on section dependencies and context.

    Args:
        section: Current section being processed
        all_sections: List of all sections (for dependency lookup)
        include_keywords: Whether to include technical keywords

    Returns:
        str: Comma-separated criteria for memorize_to
    """
    criteria_parts = []

    # Add dependency section IDs
    dependencies = section.get("prompt_context", {}).get("dependencies", [])
    for dep in dependencies:
        criteria_parts.append(dep)

    # Add component type
    component_type = section.get("prompt_context", {}).get("component_type", "")
    if component_type:
        criteria_parts.append(component_type)

    # Add key technical terms from the section
    if include_keywords:
        section_id = section.get("id", "")

        # Map section IDs to relevant technical keywords
        keyword_map = {
            "component-requirements": ["Button", "Input", "Modal", "Card", "component", "props", "TypeScript"],
            "technical-specifications": ["React", "TypeScript", "Router", "API", "Query", "Suspense", "lazy"],
            "design-system-integration": ["Tailwind", "theme", "dark mode", "tokens", "CSS", "colors"],
            "state-management": ["Context", "useReducer", "TanStack", "Query", "state", "dispatch", "hooks"],
            "error-handling": ["ErrorBoundary", "fallback", "retry", "recovery", "error"],
            "performance-considerations": ["memo", "lazy", "Suspense", "virtualization", "optimization"],
            "accessibility-requirements": ["ARIA", "keyboard", "focus", "a11y", "screen reader"],
            "testing-guidelines": ["test", "mock", "Vitest", "RTL", "coverage"]
        }

        if section_id in keyword_map:
            criteria_parts.extend(keyword_map[section_id])

    # Remove duplicates while preserving order
    seen = set()
    unique_criteria = []
    for item in criteria_parts:
        if item.lower() not in seen:
            seen.add(item.lower())
            unique_criteria.append(item)

    return ", ".join(unique_criteria)


def get_section_priority_order(sections):
    """
    Sort sections by priority for sequential processing.

    Args:
        sections: List of section objects

    Returns:
        List of sections sorted by priority (1 = highest)
    """
    return sorted(sections, key=lambda s: (s.get("priority", 999), sections.index(s)))


def extract_generated_files_keywords(generated_code):
    """
    Extract relevant keywords from generated code for future reference.

    Args:
        generated_code: The code generated for a section

    Returns:
        List of relevant keywords/identifiers
    """
    keywords = []

    # Extract component names (simple pattern matching)
    import re

    # Find exported components/functions
    export_pattern = r'export\s+(?:const|function|class)\s+(\w+)'
    exports = re.findall(export_pattern, generated_code)
    keywords.extend(exports)

    # Find interface/type definitions
    type_pattern = r'(?:interface|type)\s+(\w+)'
    types = re.findall(type_pattern, generated_code)
    keywords.extend(types)

    # Find React component definitions
    component_pattern = r'(?:const|function)\s+(\w+):\s*(?:React\.)?FC'
    components = re.findall(component_pattern, generated_code)
    keywords.extend(components)

    return list(set(keywords))  # Remove duplicates


def calculate_memory_limit(section_index, total_sections):
    """
    Calculate appropriate at_most value based on section position.

    Args:
        section_index: Current section index
        total_sections: Total number of sections

    Returns:
        int: Suggested at_most value for memory limit
    """
    # Start with fewer memories, gradually increase
    if section_index <= 2:
        return 3  # First few sections need less context
    elif section_index <= 5:
        return 5  # Middle sections need moderate context
    else:
        return 8  # Later sections may need more context
