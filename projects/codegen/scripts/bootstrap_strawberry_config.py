#!/usr/bin/env python3
"""
Bootstrap script to extract hard-coded field tables from generate_graphql_domain.py
to YAML configuration files. This is a one-time migration script.
"""

import yaml
from pathlib import Path

def extract_domain_fields_config():
    """Extract all hard-coded field configurations to YAML."""

    # Define all the field configurations from generate_graphql_domain.py
    domain_fields = {
        "interfaces": {
            # Simple types (use all_fields=True)
            "Vec2": {
                "simple_fields": True,
                "custom_fields": [],
                "field_methods": []
            },
            "LLMUsage": {
                "simple_fields": True,
                "custom_fields": [],
                "field_methods": []
            },
            "PersonLLMConfig": {
                "simple_fields": True,
                "custom_fields": [],
                "field_methods": []
            },
            "DomainHandle": {
                "simple_fields": True,
                "custom_fields": [],
                "field_methods": []
            },
            "DomainApiKey": {
                "simple_fields": True,
                "custom_fields": [],
                "field_methods": []
            },
            "FileType": {
                "simple_fields": True,
                "custom_fields": [],
                "field_methods": []
            },
            "CliSessionType": {
                "simple_fields": True,
                "custom_fields": [],
                "field_methods": []
            },
            "DiagramMetadata": {
                "simple_fields": True,
                "custom_fields": [],
                "field_methods": []
            },

            # Complex types with custom fields
            "NodeState": {
                "simple_fields": False,
                "custom_fields": [
                    {"name": "status", "is_auto": False, "is_enum": True, "type": "Status"},
                    {"name": "started_at", "is_auto": True},
                    {"name": "ended_at", "is_auto": True},
                    {"name": "error", "is_auto": True},
                    {"name": "llm_usage", "is_auto": True},
                ],
                "field_methods": [
                    {
                        "name": "output",
                        "return_type": "Optional[JSONScalar]",
                        "is_optional": True,
                        "description": "Node output data",
                    }
                ]
            },

            "EnvelopeMeta": {
                "simple_fields": False,
                "custom_fields": [
                    {
                        "name": "node_id",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[str]",
                        "default": "None",
                    },
                    {
                        "name": "llm_usage",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[LLMUsageType]",
                        "default": "None",
                    },
                    {
                        "name": "execution_time",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[float]",
                        "default": "None",
                    },
                    {
                        "name": "retry_count",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[int]",
                        "default": "None",
                    },
                    {
                        "name": "error",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[str]",
                        "default": "None",
                    },
                    {
                        "name": "error_type",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[str]",
                        "default": "None",
                    },
                    {
                        "name": "timestamp",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[JSONScalar]",
                        "default": "None",
                    }
                ],
                "field_methods": []
            },

            "SerializedEnvelope": {
                "simple_fields": False,
                "custom_fields": [
                    {"name": "envelope_format", "is_auto": True},
                    {"name": "id", "is_auto": True},
                    {"name": "trace_id", "is_auto": True},
                    {"name": "produced_by", "is_auto": True},
                    {"name": "content_type", "is_auto": True},
                    {"name": "schema_id", "is_auto": True},
                    {"name": "serialization_format", "is_auto": True},
                    {
                        "name": "body",
                        "is_auto": False,
                        "is_optional": True,
                        "type": "Optional[JSONScalar]",
                        "default": "None",
                    },
                    {"name": "meta", "is_auto": True},
                ],
                "field_methods": []
            },

            "DomainNode": {
                "simple_fields": False,
                "custom_fields": [
                    {"name": "id", "is_auto": True},
                    {"name": "position", "is_auto": True},
                ],
                "field_methods": [
                    {
                        "name": "type",
                        "return_type": "str",
                        "is_optional": False,
                        "description": "Return the enum value (lowercase) instead of the enum name.",
                    },
                    {
                        "name": "data",
                        "return_type": "JSONScalar",
                        "is_optional": False,
                        "description": "Node configuration data",
                    }
                ]
            },

            "DomainArrow": {
                "simple_fields": False,
                "custom_fields": [
                    {"name": "id", "is_auto": True},
                    {"name": "source", "is_auto": True},
                    {"name": "target", "is_auto": True},
                    {"name": "content_type", "is_auto": True},
                    {"name": "label", "is_auto": True},
                ],
                "field_methods": [
                    {
                        "name": "data",
                        "return_type": "Optional[JSONScalar]",
                        "is_optional": True,
                        "description": "Optional arrow data",
                    }
                ]
            },

            "DomainPerson": {
                "simple_fields": False,
                "custom_fields": [
                    {"name": "id", "is_auto": True},
                    {"name": "label", "is_auto": True},
                    {"name": "llm_config", "is_auto": True},
                ],
                "field_methods": [
                    {
                        "name": "type",
                        "return_type": "str",
                        "is_optional": False,
                        "description": "Always returns person",
                    }
                ]
            },

            "ExecutionOptions": {
                "simple_fields": False,
                "custom_fields": [
                    {"name": "mode", "is_auto": True},
                    {"name": "timeout", "is_auto": True},
                ],
                "field_methods": [
                    {
                        "name": "variables",
                        "return_type": "JSONScalar",
                        "is_optional": False,
                        "description": "Execution variables",
                    }
                ]
            },

            "ExecutionState": {
                "simple_fields": False,
                "custom_fields": [
                    {"name": "id", "is_auto": True},
                    {"name": "status", "is_auto": False, "is_enum": True, "type": "Status"},
                    {"name": "diagram_id", "is_auto": True},
                    {"name": "started_at", "is_auto": True},
                    {"name": "ended_at", "is_auto": True},
                    {"name": "llm_usage", "is_auto": True},
                    {"name": "error", "is_auto": True},
                    {"name": "duration_seconds", "is_auto": True},
                    {"name": "is_active", "is_auto": True},
                    {"name": "executed_nodes", "is_auto": True},
                ],
                "field_methods": [
                    {
                        "name": "node_states",
                        "return_type": "JSONScalar",
                        "is_optional": False,
                        "description": "Node execution states",
                    },
                    {
                        "name": "node_outputs",
                        "return_type": "JSONScalar",
                        "is_optional": False,
                        "description": "Node execution outputs",
                    },
                    {
                        "name": "variables",
                        "return_type": "Optional[JSONScalar]",
                        "is_optional": True,
                        "description": "Execution variables",
                    },
                    {
                        "name": "exec_counts",
                        "return_type": "JSONScalar",
                        "is_optional": False,
                        "description": "Node execution counts",
                    },
                    {
                        "name": "metrics",
                        "return_type": "Optional[JSONScalar]",
                        "is_optional": True,
                        "description": "Execution metrics",
                    }
                ]
            },

            "DomainDiagram": {
                "simple_fields": False,
                "has_all_fields": True,  # Special case - uses all fields but also has methods
                "custom_fields": [],
                "field_methods": [
                    {
                        "name": "nodeCount",
                        "return_type": "int",
                        "is_optional": False,
                        "description": "Returns the total number of nodes in the diagram",
                    },
                    {
                        "name": "arrowCount",
                        "return_type": "int",
                        "is_optional": False,
                        "description": "Returns the total number of arrows in the diagram",
                    }
                ]
            }
        }
    }

    return domain_fields


def main():
    """Main function to bootstrap configuration files."""

    # Create config directory
    config_dir = Path("projects/codegen/config/strawberry")
    config_dir.mkdir(parents=True, exist_ok=True)

    # Extract and save domain fields configuration
    domain_fields = extract_domain_fields_config()
    domain_fields_path = config_dir / "domain_fields_complete.yaml"

    with open(domain_fields_path, "w") as f:
        yaml.dump(domain_fields, f, default_flow_style=False, sort_keys=False)

    print(f"✓ Created {domain_fields_path}")
    print(f"  - {len(domain_fields['interfaces'])} interface configurations")

    # Count field methods and custom fields
    total_field_methods = sum(
        len(iface.get('field_methods', []))
        for iface in domain_fields['interfaces'].values()
    )
    total_custom_fields = sum(
        len(iface.get('custom_fields', []))
        for iface in domain_fields['interfaces'].values()
    )

    print(f"  - {total_field_methods} field methods")
    print(f"  - {total_custom_fields} custom field definitions")

    print("\nBootstrap complete! You can now:")
    print("1. Review the generated configuration")
    print("2. Replace hard-coded tables in generate_graphql_domain.py")
    print("3. Test the configuration-driven approach")


if __name__ == "__main__":
    main()
