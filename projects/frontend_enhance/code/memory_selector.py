"""
Memory selector helper for intelligent context selection in frontend generation.
Uses section dependencies and keywords to build memorize_to criteria.
"""

def build_memorize_criteria(section, all_sections, include_keywords=True):
    """Build memorize_to criteria based on section dependencies and context."""
    criteria_parts = []

    dependencies = section.get("prompt_context", {}).get("dependencies", [])
    for dep in dependencies:
        criteria_parts.append(dep)

    component_type = section.get("prompt_context", {}).get("component_type", "")
    if component_type:
        criteria_parts.append(component_type)

    if include_keywords:
        section_id = section.get("id", "")

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

    seen = set()
    unique_criteria = []
    for item in criteria_parts:
        if item.lower() not in seen:
            seen.add(item.lower())
            unique_criteria.append(item)

    return ", ".join(unique_criteria)


def get_section_priority_order(sections):
    """Sort sections by priority for sequential processing (1 = highest)."""
    return sorted(sections, key=lambda s: (s.get("priority", 999), sections.index(s)))


def extract_generated_files_keywords(generated_code):
    """Extract relevant keywords from generated code for future reference."""
    keywords = []
    import re

    export_pattern = r'export\s+(?:const|function|class)\s+(\w+)'
    exports = re.findall(export_pattern, generated_code)
    keywords.extend(exports)

    type_pattern = r'(?:interface|type)\s+(\w+)'
    types = re.findall(type_pattern, generated_code)
    keywords.extend(types)

    component_pattern = r'(?:const|function)\s+(\w+):\s*(?:React\.)?FC'
    components = re.findall(component_pattern, generated_code)
    keywords.extend(components)

    return list(set(keywords))


def calculate_memory_limit(section_index, total_sections):
    """Calculate appropriate at_most value based on section position.

    Gradually increases memory limit as more context accumulates.
    """
    if section_index <= 2:
        return 3
    elif section_index <= 5:
        return 5
    else:
        return 8
