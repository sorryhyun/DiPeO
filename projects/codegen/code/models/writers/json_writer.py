"""JSON writer utilities for model generation."""

import json
import os
from pathlib import Path


def write_field_configs_json(node_configs: list, base_dir: str | None = None) -> dict:
    """Write field configurations to JSON file."""
    if base_dir is None:
        base_dir = os.environ.get('DIPEO_BASE_DIR')
        if not base_dir:
            raise ValueError("DIPEO_BASE_DIR environment variable is not set")

    # Create output directory
    output_dir = Path(base_dir) / 'dipeo' / 'diagram_generated_staged'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Write JSON file
    output_path = output_dir / 'field-configs.json'
    with output_path.open('w') as f:
        json.dump(node_configs, f, indent=2)

    return {'json_path': output_path}


def main(inputs: dict) -> dict:
    """Main entry point for JSON writer"""
    node_configs = inputs.get('node_configs', [])
    return write_field_configs_json(node_configs)
