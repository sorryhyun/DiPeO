#!/usr/bin/env python3
"""
Hook script to inject documentation when Task tool launches agents.
Receives JSON via stdin with tool_input containing subagent_type.
"""

import json
import sys
from pathlib import Path

# Map subagent_type to documentation file(s)
# Each value can be either a single string or a list of strings
AGENT_DOCS_MAP = {
    "dipeo-package-maintainer": [
        "docs/agents/package-maintainer.md",
        "docs/architecture/README.md",
        "docs/architecture/detailed/graphql-layer.md",
    ],
    "dipeo-backend": [
        "docs/agents/backend-development.md",
        "docs/architecture/README.md",
        "docs/features/mcp-server-integration.md",
        "docs/database-schema.md",
    ],
    "dipeo-codegen-pipeline": [
        "docs/agents/codegen-pipeline.md",
        "docs/projects/code-generation-guide.md",
        "docs/architecture/README.md",
        "docs/architecture/detailed/graphql-layer.md",
    ],
    "dipeo-frontend-dev": [
        "docs/agents/frontend-development.md",
        "docs/architecture/detailed/graphql-layer.md",
        "docs/architecture/README.md",
    ],
    "codebase-auditor": [
        "docs/agents/code-auditing.md",
        "docs/architecture/README.md",
    ],
    "dipeocc-converter": [
        "docs/agents/dipeocc-conversion.md",
        "docs/projects/dipeocc-guide.md",
        "docs/formats/comprehensive_light_diagram_guide.md",
        "docs/features/claude-code-integration.md",
    ],
}


def main():
    try:
        # Read JSON input from stdin
        input_data = json.load(sys.stdin)

        # Extract subagent_type from tool_input
        tool_input = input_data.get("tool_input", {})
        subagent_type = tool_input.get("subagent_type")

        # If no subagent_type, exit silently
        if not subagent_type:
            sys.exit(0)

        # Get corresponding doc file(s)
        doc_files = AGENT_DOCS_MAP.get(subagent_type)
        if not doc_files:
            # Unknown agent, exit silently
            sys.exit(0)

        # Normalize to list
        if isinstance(doc_files, str):
            doc_files = [doc_files]

        # Read all documentation files and concatenate
        doc_contents = []
        for doc_file in doc_files:
            doc_path = Path(doc_file)
            if doc_path.exists():
                content = doc_path.read_text()
                # Add a separator between multiple docs
                if doc_contents:
                    doc_contents.append(f"\n\n---\n# {doc_path.name}\n---\n\n")
                doc_contents.append(content)

        # If no docs found, exit silently
        if not doc_contents:
            sys.exit(0)

        doc_content = "".join(doc_contents)

        # Inject docs into the prompt via updatedInput
        updated_prompt = f"""<agent_instruction>
{tool_input.get('prompt', '')}
</agent_instruction>
<agent_documentation>
{doc_content}
</agent_documentation>"""

        # Create updated tool input with docs prepended to prompt
        updated_input = {**tool_input, "prompt": updated_prompt}

        # Output JSON with updatedInput
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "updatedInput": updated_input,
            }
        }

        print(json.dumps(output))

    except Exception as e:
        # On error, exit silently (don't break the tool execution)
        sys.exit(0)


if __name__ == "__main__":
    main()
