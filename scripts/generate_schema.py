#!/usr/bin/env python3
"""
Standalone script to generate comprehensive JSON Schema for light diagram format.
This script doesn't require full DiPeO installation - it works standalone.
"""

import json
from pathlib import Path


def generate_light_diagram_schema() -> dict:
    """Generate comprehensive JSON Schema for light diagram format."""

    # List of all supported node types
    node_types = [
        "start",
        "endpoint",
        "person_job",
        "code_job",
        "condition",
        "api_job",
        "db",
        "user_response",
        "hook",
        "template_job",
        "sub_diagram",
        "json_schema_validator",
        "typescript_ast",
        "integrated_api",
        "ir_builder",
        "diff_patch",
    ]

    # Comprehensive node-specific property schemas
    node_property_schemas = {
        "start": {
            "description": "Entry point for diagram execution",
            "properties": {
                "trigger_mode": {
                    "type": "string",
                    "enum": ["manual", "automatic"],
                    "description": "How the diagram is triggered",
                },
                "custom_data": {
                    "type": "object",
                    "description": "Initial variables available to all nodes",
                },
            },
        },
        "endpoint": {
            "description": "Save results to files",
            "properties": {
                "file_format": {
                    "type": "string",
                    "enum": ["txt", "json", "yaml", "md"],
                    "description": "Output file format",
                },
                "save_to_file": {"type": "boolean", "description": "Whether to save to file"},
                "file_path": {
                    "type": "string",
                    "description": "Output file path (relative to project root)",
                },
                "file_name": {
                    "type": "string",
                    "description": "Alternative to file_path (backward compatible)",
                },
            },
        },
        "person_job": {
            "description": "Execute prompts with LLM agents",
            "properties": {
                "person": {"type": "string", "description": "AI agent identifier from persons section"},
                "default_prompt": {"type": "string", "description": "Prompt template (supports {{variables}})"},
                "first_only_prompt": {
                    "type": "string",
                    "description": "Prompt used only on first iteration",
                },
                "prompt_file": {
                    "type": "string",
                    "description": "Path to prompt file in /files/prompts/",
                },
                "first_prompt_file": {
                    "type": "string",
                    "description": "Path to first prompt file in /files/prompts/",
                },
                "max_iteration": {
                    "type": "integer",
                    "minimum": 1,
                    "description": "Maximum execution iterations",
                },
                "memorize_to": {
                    "type": "string",
                    "description": "Memory selection criteria (e.g. 'requirements, feedback')",
                },
                "at_most": {
                    "type": "number",
                    "description": "Maximum messages to keep in memory",
                },
                "ignore_person": {
                    "type": "string",
                    "description": "Comma-separated person IDs to exclude from memory",
                },
                "tools": {
                    "anyOf": [
                        {"type": "string", "enum": ["none", "image", "websearch"]},
                        {"type": "array", "items": {"type": "object"}},
                    ],
                    "description": "Tools available to AI agent",
                },
                "text_format": {"type": "string", "description": "JSON schema for structured outputs"},
                "text_format_file": {
                    "type": "string",
                    "description": "Path to Pydantic models file for structured outputs",
                },
                "batch": {"type": "boolean", "description": "Enable batch mode"},
                "batch_input_key": {
                    "type": "string",
                    "description": "Key containing array to iterate over",
                },
                "batch_parallel": {
                    "type": "boolean",
                    "description": "Execute batch items in parallel",
                },
            },
            "required": ["max_iteration"],
        },
        "code_job": {
            "description": "Execute code in various languages",
            "properties": {
                "language": {
                    "type": "string",
                    "enum": ["python", "typescript", "javascript", "bash", "shell"],
                    "description": "Programming language",
                },
                "code_type": {
                    "type": "string",
                    "description": "Alternative to language (backward compatible)",
                },
                "code": {
                    "type": "string",
                    "description": "Inline code or path to external file",
                },
                "filePath": {"type": "string", "description": "Path to external code file"},
                "functionName": {
                    "type": "string",
                    "description": "Function name to call (for external files)",
                },
            },
        },
        "condition": {
            "description": "Control flow based on conditions",
            "properties": {
                "condition_type": {
                    "type": "string",
                    "enum": ["detect_max_iterations", "nodes_executed", "custom", "llm_decision"],
                    "description": "Type of condition to evaluate",
                },
                "expression": {
                    "type": "string",
                    "description": "Python expression for custom conditions",
                },
                "flipped": {
                    "anyOf": [
                        {"type": "boolean"},
                        {"type": "array", "items": {"type": "boolean"}},
                    ],
                    "description": "Invert true/false outputs",
                },
                "person": {
                    "type": "string",
                    "description": "AI agent for llm_decision conditions",
                },
                "judge_by": {
                    "type": "string",
                    "description": "Prompt for llm_decision evaluation",
                },
                "judge_by_file": {
                    "type": "string",
                    "description": "Path to prompt file for llm_decision",
                },
                "memorize_to": {
                    "type": "string",
                    "description": "Memory criteria for llm_decision",
                },
            },
        },
        "api_job": {
            "description": "HTTP API requests",
            "properties": {
                "url": {"type": "string", "description": "Request URL (supports {{variables}})"},
                "method": {
                    "type": "string",
                    "enum": ["GET", "POST", "PUT", "DELETE", "PATCH"],
                    "description": "HTTP method",
                },
                "headers": {
                    "type": "object",
                    "description": "Request headers (supports {{variables}})",
                },
                "body": {
                    "anyOf": [
                        {"type": "object"},
                        {"type": "string"},
                    ],
                    "description": "Request body (supports {{variables}})",
                },
                "timeout": {"type": "number", "description": "Request timeout in seconds"},
            },
        },
        "db": {
            "description": "File system operations",
            "properties": {
                "operation": {
                    "type": "string",
                    "enum": ["read", "write"],
                    "description": "Operation type",
                },
                "sub_type": {"type": "string", "enum": ["file"], "description": "Database sub-type"},
                "file": {
                    "anyOf": [
                        {"type": "string"},
                        {"type": "array", "items": {"type": "string"}},
                    ],
                    "description": "File path(s) or glob pattern(s)",
                },
                "source_details": {
                    "type": "string",
                    "description": "Alternative to file (backward compatible)",
                },
                "glob": {
                    "type": "boolean",
                    "description": "Enable glob pattern expansion",
                },
                "serialize_json": {
                    "type": "boolean",
                    "description": "Auto-parse JSON files",
                },
            },
        },
        "sub_diagram": {
            "description": "Execute another diagram as a node",
            "properties": {
                "diagram_name": {"type": "string", "description": "Path to sub-diagram"},
                "diagram_format": {
                    "type": "string",
                    "enum": ["light", "readable"],
                    "description": "Sub-diagram format",
                },
                "passInputData": {
                    "type": "boolean",
                    "description": "Pass all variables to sub-diagram",
                },
                "batch": {"type": "boolean", "description": "Execute once per array item"},
                "batch_input_key": {
                    "type": "string",
                    "description": "Array variable for batching",
                },
                "batch_parallel": {
                    "type": "boolean",
                    "description": "Run batch items concurrently",
                },
            },
        },
        "template_job": {
            "description": "Advanced template rendering with Jinja2",
            "properties": {
                "engine": {
                    "type": "string",
                    "enum": ["jinja2"],
                    "description": "Template engine",
                },
                "template_path": {
                    "type": "string",
                    "description": "Path to template file",
                },
                "output_path": {"type": "string", "description": "Output file path"},
                "variables": {
                    "type": "object",
                    "description": "Template variables (supports {{variables}})",
                },
            },
        },
        "user_response": {
            "description": "Interactive user input",
            "properties": {
                "prompt": {"type": "string", "description": "Prompt to display to user"},
                "timeout": {"type": "number", "description": "Input timeout in seconds"},
                "validation_type": {
                    "type": "string",
                    "enum": ["text", "number", "boolean"],
                    "description": "Expected input type",
                },
            },
        },
        "hook": {
            "description": "Execute external hooks",
            "properties": {
                "hook_type": {
                    "type": "string",
                    "enum": ["shell", "webhook", "python"],
                    "description": "Hook type",
                },
                "config": {
                    "type": "object",
                    "description": "Hook-specific configuration",
                },
            },
        },
        "json_schema_validator": {
            "description": "Validate JSON against schema",
            "properties": {
                "schema": {
                    "type": "object",
                    "description": "JSON Schema for validation",
                },
                "strict": {
                    "type": "boolean",
                    "description": "Fail on validation errors",
                },
                "strict_mode": {
                    "type": "boolean",
                    "description": "Alternative to strict (backward compatible)",
                },
            },
        },
        "typescript_ast": {
            "description": "Parse and analyze TypeScript code",
            "properties": {
                "source_file": {
                    "type": "string",
                    "description": "TypeScript file to parse",
                },
                "extract": {
                    "type": "array",
                    "items": {
                        "type": "string",
                        "enum": ["interfaces", "functions", "exports", "classes"],
                    },
                    "description": "Elements to extract",
                },
            },
        },
        "integrated_api": {
            "description": "Pre-configured API integrations",
            "properties": {
                "provider": {
                    "type": "string",
                    "enum": ["notion", "slack", "github"],
                    "description": "API provider",
                },
                "operation": {"type": "string", "description": "Provider-specific operation"},
                "config": {
                    "type": "object",
                    "description": "Operation configuration",
                },
                "api_key_id": {
                    "type": "string",
                    "description": "API key reference",
                },
            },
        },
        "ir_builder": {
            "description": "Build intermediate representation",
            "properties": {
                "builder_type": {"type": "string", "description": "IR builder type"},
                "config": {"type": "object", "description": "Builder configuration"},
            },
        },
        "diff_patch": {
            "description": "Apply diff patches to files",
            "properties": {
                "patch": {"type": "string", "description": "Unified diff patch content"},
                "target_file": {"type": "string", "description": "Target file path"},
            },
        },
    }

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
                                    "properties": {
                                        "type": {"const": node_type}
                                    },
                                    "required": ["type"],
                                },
                                "then": {
                                    "properties": node_property_schemas[node_type].get("properties", {}),
                                    "required": node_property_schemas[node_type].get("required", []),
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
                            "description": "Source node label, optionally with handle (e.g. 'node_condtrue')",
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
            "nodePropertySchemas": node_property_schemas,
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
            "fieldAliases": {
                "description": "DiPeO supports field aliases for backward compatibility",
                "mappings": {
                    "code_job": {"language": "code_type"},
                    "db": {"file": "source_details"},
                    "endpoint": {"file_path": "file_name"},
                    "json_schema_validator": {"strict": "strict_mode"},
                },
            },
        },
    }

    return schema


def main():
    """Generate and save the schema."""
    project_root = Path(__file__).parent.parent
    schema_dir = project_root / "dipeo" / "diagram_generated" / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)

    output_file = schema_dir / "dipeo-light.schema.json"

    schema = generate_light_diagram_schema()

    with open(output_file, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"✅ Generated comprehensive light diagram schema:")
    print(f"   📁 {output_file}")
    print(f"   📦 {len(schema['$defs']['nodePropertySchemas'])} node types with full property definitions")
    print(f"   ✨ Shorthand notation support")
    print(f"   🔄 Field alias mappings")
    print()
    print("To use this schema in your diagrams, add this line at the top:")
    print('  $schema: "https://dipeo.dev/schemas/light-v1.json"')
    print()
    print("For VSCode, this enables:")
    print("  • Auto-completion of node types and properties")
    print("  • Real-time validation")
    print("  • Inline documentation")


if __name__ == "__main__":
    main()
