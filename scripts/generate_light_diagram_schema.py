#!/usr/bin/env python3
"""
Generate comprehensive JSON Schema for light diagram format.
Uses auto-generated node schemas from TypeScript specs as the source of truth.
"""

import json
from pathlib import Path


def load_generated_node_schemas(schemas_dir: Path) -> dict[str, dict]:
    """Load all generated node schemas from schemas/nodes/ directory.

    Returns:
        Dict mapping node_type (snake_case) to node schema properties
    """
    node_schemas_dir = schemas_dir / "nodes"
    if not node_schemas_dir.exists():
        raise FileNotFoundError(
            f"Node schemas directory not found: {node_schemas_dir}\n"
            "Run 'make codegen' first to generate node schemas."
        )

    node_schemas = {}

    for schema_file in node_schemas_dir.glob("*.schema.json"):
        # Extract node type from filename (e.g., personjob.schema.json -> person_job)
        filename = schema_file.stem.replace(".schema", "")

        # Convert camelCase to snake_case
        node_type = ""
        for i, char in enumerate(filename):
            if char.isupper() and i > 0:
                node_type += "_"
            node_type += char.lower()

        # Load the schema
        with open(schema_file) as f:
            schema_data = json.load(f)

        # Extract the main definition (usually the first one, e.g., "PersonJobNodeData")
        definitions = schema_data.get("definitions", {})
        if not definitions:
            print(f"Warning: No definitions found in {schema_file.name}, skipping")
            continue

        # Get the primary definition (the one referenced by $ref)
        ref = schema_data.get("$ref", "")
        if ref.startswith("#/definitions/"):
            main_def_name = ref.split("/")[-1]
            main_def = definitions.get(main_def_name, {})
        else:
            # Fallback: use the first definition
            main_def = next(iter(definitions.values()))

        # Extract properties and required fields
        properties = main_def.get("properties", {})
        required = main_def.get("required", [])
        description = main_def.get("description", f"Configuration for {node_type} nodes")

        # Filter out common node fields that are handled at diagram level
        excluded_fields = {"label", "flipped", "metadata"}
        filtered_properties = {k: v for k, v in properties.items() if k not in excluded_fields}
        filtered_required = [r for r in required if r not in excluded_fields]

        node_schemas[node_type] = {
            "description": description,
            "properties": filtered_properties,
            "required": filtered_required,
        }

    return node_schemas


def generate_light_diagram_schema(node_schemas: dict[str, dict]) -> dict:
    """Generate comprehensive JSON Schema for light diagram format.

    Args:
        node_schemas: Dict mapping node_type to node schema definition
    """
    node_types = list(node_schemas.keys())

    # Main schema structure
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "$id": "https://dipeo.dev/schemas/light-v1.json",
        "title": "DiPeO Light Diagram Schema",
        "description": "Comprehensive schema for DiPeO light diagram format with full node type validation and shorthand notation support",
        "type": "object",
        "required": ["version", "nodes"],
        "properties": {
            "$schema": {
                "type": "string",
                "description": "JSON Schema reference URL (optional)",
            },
            "version": {
                "type": "string",
                "const": "light",
                "description": "Diagram format version (must be 'light')",
            },
            "metadata": {
                "type": "object",
                "description": "Optional diagram metadata for documentation",
                "properties": {
                    "name": {"type": "string", "description": "Diagram name"},
                    "description": {"type": "string", "description": "Diagram description"},
                    "author": {"type": "string", "description": "Author name or email"},
                    "version": {"type": "string", "description": "Diagram version"},
                    "created": {"type": "string", "description": "Creation date"},
                    "modified": {"type": "string", "description": "Last modified date"},
                    "tags": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Searchable tags",
                    },
                },
            },
            "persons": {
                "type": "object",
                "description": "AI agents/personas used in the diagram",
                "additionalProperties": {
                    "type": "object",
                    "required": ["service", "model"],
                    "properties": {
                        "service": {
                            "type": "string",
                            "enum": ["openai", "anthropic", "ollama", "gemini"],
                            "description": "LLM service provider",
                        },
                        "model": {
                            "type": "string",
                            "description": "Model identifier (e.g. gpt-5-nano-2025-08-07)",
                        },
                        "api_key_id": {
                            "type": "string",
                            "description": "API key reference from api_keys section",
                        },
                        "system_prompt": {
                            "type": "string",
                            "description": "System prompt defining agent's role and behavior",
                        },
                    },
                },
            },
            "api_keys": {
                "type": "array",
                "description": "API key definitions (stored securely, not in diagram files)",
                "items": {
                    "type": "object",
                    "required": ["id", "service"],
                    "properties": {
                        "id": {"type": "string", "description": "Unique key identifier"},
                        "service": {
                            "type": "string",
                            "description": "Service this key is for",
                        },
                    },
                },
            },
            "nodes": {
                "type": "array",
                "description": "Execution nodes in the diagram",
                "minItems": 1,
                "items": {
                    "allOf": [
                        {
                            # Base node schema with common properties
                            "type": "object",
                            "required": ["label", "type", "position"],
                            "properties": {
                                "label": {
                                    "type": "string",
                                    "description": "Human-readable node identifier (must be unique)",
                                },
                                "type": {
                                    "type": "string",
                                    "enum": node_types,
                                    "description": "Node type determining behavior and available properties",
                                },
                                "position": {
                                    "type": "object",
                                    "required": ["x", "y"],
                                    "properties": {
                                        "x": {
                                            "type": "number",
                                            "description": "X coordinate for visual positioning",
                                        },
                                        "y": {
                                            "type": "number",
                                            "description": "Y coordinate for visual positioning",
                                        },
                                    },
                                    "description": "Visual position in diagram editor",
                                },
                                "flipped": {
                                    "anyOf": [
                                        {"type": "boolean"},
                                        {
                                            "type": "array",
                                            "items": {"type": "boolean"},
                                            "minItems": 2,
                                            "maxItems": 2,
                                        },
                                    ],
                                    "description": "Handle flip configuration for visual layout",
                                },
                                "metadata": {
                                    "type": "object",
                                    "description": "Additional node metadata",
                                },
                                "props": {
                                    "type": "object",
                                    "description": "Node properties (traditional style) - use shorthand notation by specifying properties directly without props wrapper",
                                },
                            },
                            "additionalProperties": True,  # Allow shorthand properties
                        },
                        # Conditional schemas for each node type
                        *[
                            {
                                "if": {
                                    "properties": {"type": {"const": node_type}},
                                    "required": ["type"],
                                },
                                "then": {
                                    "properties": node_schemas[node_type].get("properties", {}),
                                    "required": node_schemas[node_type].get("required", []),
                                },
                            }
                            for node_type in node_types
                        ],
                    ],
                },
            },
            "connections": {
                "type": "array",
                "description": "Data flow connections between nodes",
                "items": {
                    "type": "object",
                    "required": ["from", "to"],
                    "properties": {
                        "from": {
                            "type": "string",
                            "description": "Source node label, optionally with handle (e.g. 'node_cond→true')",
                        },
                        "to": {
                            "type": "string",
                            "description": "Target node label",
                        },
                        "label": {
                            "type": "string",
                            "description": "Variable name accessible in target node (critical for data flow)",
                        },
                        "content_type": {
                            "type": "string",
                            "enum": ["raw_text", "conversation_state", "object"],
                            "description": "Data transformation type between nodes",
                        },
                        "type": {
                            "type": "string",
                            "description": "Alias for content_type (backward compatible)",
                        },
                    },
                    "additionalProperties": False,
                },
            },
        },
        # Store node-specific schemas for reference and future IDE integration
        "$defs": {
            "nodePropertySchemas": node_schemas,
            "shorthandNotation": {
                "description": "DiPeO supports shorthand notation where node properties can be specified directly without the 'props:' wrapper. Any field that is not 'type', 'label', 'position', 'flipped', or 'metadata' will be collected into the node's properties.",
                "examples": [
                    {
                        "traditional": {
                            "label": "analyzer",
                            "type": "person_job",
                            "position": {"x": 400, "y": 200},
                            "props": {"person": "analyst", "max_iteration": 3},
                        },
                        "shorthand": {
                            "label": "analyzer",
                            "type": "person_job",
                            "position": {"x": 400, "y": 200},
                            "person": "analyst",
                            "max_iteration": 3,
                        },
                    }
                ],
            },
        },
    }

    return schema


def main():
    """Generate and save the schema."""
    project_root = Path(__file__).parent.parent
    schemas_dir = project_root / "dipeo" / "diagram_generated" / "schemas"

    # Load node schemas from generated files
    print("Loading generated node schemas...")
    node_schemas = load_generated_node_schemas(schemas_dir)
    print(f"✓ Loaded {len(node_schemas)} node type schemas")

    # Generate the main diagram schema
    schema = generate_light_diagram_schema(node_schemas)

    # Save to output file
    output_file = schemas_dir / "dipeo-light.schema.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w") as f:
        json.dump(schema, f, indent=2)

    print("\n✅ Generated comprehensive light diagram schema:")
    print(f"   📁 {output_file}")
    print(f"   📦 {len(node_schemas)} node types with auto-extracted properties")
    print("   ✨ Shorthand notation support")
    print()
    print("To use this schema in your diagrams, add this line at the top:")
    print('  $schema: "https://dipeo.dev/schemas/light-v1.json"')
    print()
    print("For IDE integration:")
    print("  • VSCode: Schema auto-detected via $schema reference")
    print("  • PyCharm: Configure in Settings → JSON Schema Mappings")
    print("  • IntelliJ: Configure in Settings → JSON Schema Mappings")


if __name__ == "__main__":
    main()
