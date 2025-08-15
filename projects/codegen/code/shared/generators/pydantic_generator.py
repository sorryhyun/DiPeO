"""Generate Pydantic models from JSON schemas."""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
import time


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Generate Pydantic models from JSON schemas.
    
    Args:
        inputs: Dictionary containing:
            - schemas_dir: Path to directory containing JSON schemas
            
    Returns:
        Dictionary with generated Pydantic models
    """
    base_dir_env = os.environ.get('DIPEO_BASE_DIR')
    if not base_dir_env:
        raise ValueError("DIPEO_BASE_DIR environment variable is not set")
    base_dir = Path(base_dir_env)
    
    # Input schemas directory
    schemas_dir = base_dir / 'dipeo' / 'diagram_generated_staged' / 'schemas' / 'nodes'
    
    # Output directory
    output_dir = base_dir / 'dipeo' / 'diagram_generated_staged' / 'validation' / 'nodes'
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # First, ensure datamodel-code-generator is installed
    try:
        import datamodel_code_generator
    except ImportError:
        raise ImportError(
            "datamodel-code-generator is not installed. "
            "Please run: uv add datamodel-code-generator"
        )
    
    def process_schema(schema_file: Path) -> Tuple[str, str, bool, str]:
        """Process a single schema file and return (model_name, output_path, success, error_msg)."""
        model_name = schema_file.stem.replace('.schema', '')
        output_file = output_dir / f"{model_name}_models.py"
        
        # Generate Pydantic models
        cmd = [
            'datamodel-codegen',
            '--input', str(schema_file),
            '--output', str(output_file),
            '--use-schema-description',
            '--field-constraints',
            '--use-default',
            '--target-python-version', '3.10',
            '--input-file-type', 'jsonschema',
            '--output-model-type', 'pydantic_v2.BaseModel'
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            # Post-process the generated file to add validation imports
            with open(output_file, 'r') as f:
                content = f.read()
            
            # Add validation imports and custom validators if needed
            # Check if content contains future annotations import
            if 'from __future__ import annotations' in content:
                # Already has the import, just add our header
                new_content = """# Auto-generated from JSON Schema
# DO NOT EDIT MANUALLY

""" + content
            else:
                # Add our standard imports
                new_content = """# Auto-generated from JSON Schema
# DO NOT EDIT MANUALLY

from __future__ import annotations

""" + content
            
            with open(output_file, 'w') as f:
                f.write(new_content)
            
            return model_name, str(output_file), True, ""
                
        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to generate {model_name}: {e.stderr}"
            return model_name, "", False, error_msg
    
    # Collect all schema files
    schema_files = list(schemas_dir.glob('*.schema.json'))
    models_generated = {}
    errors = []
    
    # Process files in parallel
    start_time = time.time()
    max_workers = max(1, min(8, len(schema_files)))  # Ensure at least 1 worker
    
    if not schema_files:
        print(f"Warning: No schema files found in {schemas_dir}")
        return {
            'models_generated': {},
            'errors': [f"No schema files found in {schemas_dir}"],
            'elapsed_time': 0.0
        }
    
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_file = {executor.submit(process_schema, f): f for f in schema_files}
        
        # Process results as they complete
        for future in as_completed(future_to_file):
            schema_file = future_to_file[future]
            try:
                model_name, output_path, success, error_msg = future.result()
                if success:
                    models_generated[model_name] = output_path
                else:
                    errors.append(error_msg)
            except Exception as e:
                error_msg = f"Unexpected error processing {schema_file.name}: {str(e)}"
                errors.append(error_msg)
    
    # Create __init__.py to export all models
    init_file = output_dir / '__init__.py'
    init_content = '"""Pydantic validation models for GraphQL v2."""\n\n'
    
    for model_name in sorted(models_generated.keys()):
        init_content += f'from .{model_name}_models import *\n'
    
    with open(init_file, 'w') as f:
        f.write(init_content)
    
    elapsed_time = time.time() - start_time
    print(f"Pydantic models: {len(models_generated)} files - done!")
    
    # Generate a combined validation module
    combined_file = output_dir / 'node_validators.py'
    validator_content = """# Combined node validators for GraphQL v2
from typing import Dict, Type
from pydantic import BaseModel

# Import all node models
"""
    
    node_validators = {}
    for model_name in sorted(models_generated.keys()):
        # The datamodel-codegen generates a class named 'Model' in each file
        # We'll rename it during import
        module_alias = ''.join(word.capitalize() for word in model_name.split('_')) + 'NodeData'
        validator_content += f'from .{model_name}_models import Model as {module_alias}\n'
        node_validators[model_name] = module_alias
    
    validator_content += '\n# Validator mapping\nNODE_VALIDATORS: Dict[str, Type[BaseModel]] = {\n'
    for node_type, class_name in node_validators.items():
        validator_content += f'    "{node_type}": {class_name},\n'
    validator_content += '}\n\n'
    
    validator_content += """def validate_node_data(node_type: str, data: dict) -> BaseModel:
    \"\"\"Validate node data against its schema.\"\"\"
    validator_class = NODE_VALIDATORS.get(node_type)
    if not validator_class:
        raise ValueError(f"No validator found for node type: {node_type}")
    
    return validator_class(**data)
"""
    
    with open(combined_file, 'w') as f:
        f.write(validator_content)
    
    print(f"✓ Generated combined validator module: {combined_file.name}")
    
    return {
        'status': 'success' if not errors else 'partial',
        'message': f'Generated {len(models_generated)} Pydantic model files',
        'models_generated': models_generated,
        'errors': errors,
        'output_dir': str(output_dir)
    }