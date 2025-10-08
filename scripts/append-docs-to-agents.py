#!/usr/bin/env python3
"""
Append documentation content to agent definition files.
This embeds the documentation directly into each agent's .md file.
"""

from pathlib import Path

# Map subagent_type to documentation file(s) - same as in inject-agent-docs.py
AGENT_DOCS_MAP = {
    "dipeo-codegen-specialist": [
        "docs/agents/codegen-pipeline.md",
        "docs/projects/code-generation-guide.md",
        "docs/architecture/overall_architecture.md",
        "docs/formats/comprehensive_light_diagram_guide.md",
    ],
    "typescript-model-designer": [
        "docs/agents/typescript-model-design.md",
        "docs/projects/code-generation-guide.md",
        "docs/architecture/graphql-layer.md",
    ],
    "dipeo-core-python": [
        "docs/agents/core-python-development.md",
        "docs/architecture/overall_architecture.md",
        "docs/architecture/graphql-layer.md",
        "docs/projects/code-generation-guide.md",
    ],
    "dipeo-frontend-dev": [
        "docs/agents/frontend-development.md",
        "docs/architecture/graphql-layer.md",
        "docs/architecture/overall_architecture.md",
    ],
    "comment-cleaner": "docs/agents/comment-cleanup.md",
    "codebase-auditor": [
        "docs/agents/code-auditing.md",
        "docs/architecture/overall_architecture.md",
    ],
    "typecheck-fixer": [
        "docs/agents/typecheck-fixing.md",
        "docs/agents/frontend-development.md",
        "docs/architecture/graphql-layer.md",
    ],
    "docs-maintainer": [
        "docs/agents/documentation-maintenance.md",
        "docs/index.md",
    ],
    "todo-manager": "docs/agents/task-management.md",
    "dipeocc-converter": [
        "docs/agents/dipeocc-conversion.md",
        "docs/projects/dipeocc-guide.md",
        "docs/formats/comprehensive_light_diagram_guide.md",
        "docs/integrations/claude-code.md",
    ],
    "import-refactor-updater": [
        "docs/agents/import-refactoring.md",
        "docs/architecture/overall_architecture.md",
    ],
    "chatgpt-DiPeO-project-manager": "docs/agents/chatgpt-integration.md",
}


def append_docs_to_agent(agent_name: str, doc_files: list[str] | str) -> None:
    """Append documentation to an agent definition file."""
    agent_file = Path(f".claude/agents/{agent_name}.md")

    if not agent_file.exists():
        print(f"⚠️  Agent file not found: {agent_file}")
        return

    # Normalize to list
    if isinstance(doc_files, str):
        doc_files = [doc_files]

    # Read all documentation files
    doc_contents = []
    for doc_file in doc_files:
        doc_path = Path(doc_file)
        if doc_path.exists():
            content = doc_path.read_text()
            # Add separator between multiple docs
            if doc_contents:
                doc_contents.append(f"\n\n---\n# {doc_path.name}\n---\n\n")
            doc_contents.append(content)
        else:
            print(f"⚠️  Documentation file not found: {doc_path}")

    if not doc_contents:
        print(f"⚠️  No documentation found for agent: {agent_name}")
        return

    # Read current agent content
    current_content = agent_file.read_text()

    # Check if docs are already appended (to avoid duplication)
    if "# Embedded Documentation" in current_content:
        print(f"⏭️  Agent already has embedded docs: {agent_name}")
        return

    # Append documentation
    doc_section = "\n\n---\n\n# Embedded Documentation\n\n" + "".join(doc_contents)
    updated_content = current_content + doc_section

    # Write updated content
    agent_file.write_text(updated_content)
    print(f"✅ Updated agent: {agent_name}")


def main():
    print("📚 Appending documentation to agent definitions...\n")

    for agent_name, doc_files in AGENT_DOCS_MAP.items():
        append_docs_to_agent(agent_name, doc_files)

    print("\n✨ Done! Agent definitions updated.")
    print("📁 Backups are in .claude/agents_backup/")


if __name__ == "__main__":
    main()
