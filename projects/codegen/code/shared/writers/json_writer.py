"""JSON writer utilities for model generation."""

import json
import os


def write_field_configs_json(node_configs: list, base_dir: str = None) -> dict:
    """Write field configurations to JSON file."""
    if base_dir is None:
        base_dir = os.environ.get('DIPEO_BASE_DIR')
        if not base_dir:
            raise ValueError("DIPEO_BASE_DIR environment variable is not set")
    
    # Create output directory
    output_dir = os.path.join(base_dir, 'dipeo/diagram_generated_staged')
    os.makedirs(output_dir, exist_ok=True)
    
    # Write JSON file
    output_path = os.path.join(output_dir, 'field-configs.json')
    with open(output_path, 'w') as f:
        json.dump(node_configs, f, indent=2)
    
    print(f"Written JSON to: {output_path}")
    
    return {'json_path': output_path}


def main(inputs: dict) -> dict:
    """Main entry point for JSON writer"""
    node_configs = inputs.get('node_configs', [])
    return write_field_configs_json(node_configs)