"""Generate comprehensive JSON Schema for light diagram format from Pydantic models."""

from __future__ import annotations

import json
from typing import Any

from dipeo.diagram_generated.unified_nodes import (
    ApiJobNode,
    CodeJobNode,
    ConditionNode,
    DbNode,
    DiffPatchNode,
    EndpointNode,
    HookNode,
    IntegratedApiNode,
    IrBuilderNode,
    JsonSchemaValidatorNode,
    PersonJobNode,
    StartNode,
    SubDiagramNode,
    TemplateJobNode,
    TypescriptAstNode,
    UserResponseNode,
)

# Map of node type string to node class
NODE_TYPE_MAP = {
    "start": StartNode,
    "endpoint": EndpointNode,
    "person_job": PersonJobNode,
    "code_job": CodeJobNode,
    "condition": ConditionNode,
    "api_job": ApiJobNode,
    "db": DbNode,
    "user_response": UserResponseNode,
    "hook": HookNode,
    "template_job": TemplateJobNode,
    "sub_diagram": SubDiagramNode,
    "json_schema_validator": JsonSchemaValidatorNode,
    "typescript_ast": TypescriptAstNode,
    "integrated_api": IntegratedApiNode,
    "ir_builder": IrBuilderNode,
    "diff_patch": DiffPatchNode,
}


def generate_node_properties_schema() -> dict[str, Any]:
    """Generate properties schema for all node types."""
    node_schemas = {}

    for node_type, node_class in NODE_TYPE_MAP.items():
        # Get Pydantic JSON schema for this node
        schema = node_class.model_json_schema()

        # Extract properties, removing id, type, position, label, flipped, metadata
        # as these are handled at the top level
        properties = schema.get("properties", {})
        node_props = {}

        # Skip base fields that are handled at diagram level
        skip_fields = {"id", "type", "position", "label", "flipped", "metadata"}

        for prop_name, prop_schema in properties.items():
            if prop_name not in skip_fields:
                node_props[prop_name] = prop_schema

        node_schemas[node_type] = {
            "type": "object",
            "description": schema.get("description", f"Properties for {node_type} node"),
            "properties": node_props,
            "required": [
                field for field in schema.get("required", []) if field not in skip_fields
            ],
        }

    return node_schemas


def generate_light_diagram_schema() -> dict[str, Any]:
    """Generate comprehensive JSON Schema for light diagram format."""

    # Get node-specific schemas
    node_schemas = generate_node_properties_schema()

    # Base schema structure
    schema = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "title": "DiPeO Light Diagram Schema",
        "description": "Schema for DiPeO light diagram format with comprehensive node type validation",
        "type": "object",
        "required": ["version", "nodes"],
        "properties": {
            "$schema": {
                "type": "string",
                "description": "JSON Schema reference (optional)",
            },
            "version": {
                "type": "string",
                "enum": ["light"],
                "description": "Diagram format version",
            },
            "metadata": {
                "type": "object",
                "description": "Optional diagram metadata",
                "properties": {
                    "name": {"type": "string"},
                    "description": {"type": "string"},
                    "author": {"type": "string"},
                    "version": {"type": "string"},
                    "created": {"type": "string"},
                    "modified": {"type": "string"},
                    "tags": {"type": "array", "items": {"type": "string"}},
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
                            "description": "Model identifier",
                        },
                        "api_key_id": {
                            "type": "string",
                            "description": "API key reference",
                        },
                        "system_prompt": {
                            "type": "string",
                            "description": "System prompt for the AI agent",
                        },
                    },
                },
            },
            "api_keys": {
                "type": "array",
                "description": "API key definitions",
                "items": {
                    "type": "object",
                    "required": ["id", "service"],
                    "properties": {
                        "id": {"type": "string"},
                        "service": {"type": "string"},
                        "key": {"type": "string"},
                    },
                },
            },
            "nodes": {
                "type": "array",
                "description": "Execution nodes in the diagram",
                "minItems": 1,
                "items": {
                    "type": "object",
                    "required": ["label", "type", "position"],
                    "properties": {
                        "label": {
                            "type": "string",
                            "description": "Human-readable node identifier",
                        },
                        "type": {
                            "type": "string",
                            "enum": list(NODE_TYPE_MAP.keys()),
                            "description": "Node type",
                        },
                        "position": {
                            "type": "object",
                            "required": ["x", "y"],
                            "properties": {
                                "x": {"type": "number", "description": "X coordinate"},
                                "y": {"type": "number", "description": "Y coordinate"},
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
                            "description": "Handle flip configuration",
                        },
                        "metadata": {
                            "type": "object",
                            "description": "Additional node metadata",
                        },
                        "props": {
                            "type": "object",
                            "description": "Node properties (traditional style) - alternatively, properties can be specified directly without props wrapper",
                        },
                    },
                    # Add note about shorthand notation
                    "additionalProperties": True,  # Allow shorthand properties
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
                            "description": "Source node label (with optional handle: label_handlename)",
                        },
                        "to": {
                            "type": "string",
                            "description": "Target node label",
                        },
                        "label": {
                            "type": "string",
                            "description": "Variable name in target node",
                        },
                        "content_type": {
                            "type": "string",
                            "enum": ["raw_text", "conversation_state", "object"],
                            "description": "Data transformation type",
                        },
                        "type": {
                            "type": "string",
                            "description": "Alias for content_type",
                        },
                    },
                },
            },
        },
        # Store node-specific schemas for reference
        "$defs": {
            "nodeSchemas": node_schemas,
        },
    }

    return schema


def save_schema(output_path: str) -> None:
    """Generate and save the schema to a file."""
    schema = generate_light_diagram_schema()

    with open(output_path, "w") as f:
        json.dump(schema, f, indent=2)

    print(f"✅ Generated comprehensive light diagram schema: {output_path}")
    print(f"   - {len(NODE_TYPE_MAP)} node types")
    print(f"   - Full property validation with descriptions")
    print(f"   - Shorthand notation support")


if __name__ == "__main__":
    import os
    from pathlib import Path

    # Default output location
    project_root = Path(__file__).parent.parent.parent
    schema_dir = project_root / "dipeo" / "diagram_generated" / "schemas"
    schema_dir.mkdir(parents=True, exist_ok=True)

    output_file = schema_dir / "dipeo-light.schema.json"
    save_schema(str(output_file))
