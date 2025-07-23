"""
Helper functions for sub-diagrams to save their results.
"""
import json
import os
from typing import Dict, Any, List
from datetime import datetime


def save_domain_model_results(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Save domain model generation results to file"""
    # Get execution context from inputs
    execution_id = inputs.get('execution_id', 'unknown')
    output_dir = inputs.get('output_dir', 'logs/codegen/runs/unknown')
    
    # Read results from temp files
    temp_dir = os.getenv('DIPEO_BASE_DIR', os.getcwd())
    temp_base = os.path.join(temp_dir, '.temp', 'codegen')
    
    # Load combined results
    combined_file = os.path.join(temp_base, 'combined_results.json')
    combined_results = {}
    if os.path.exists(combined_file):
        with open(combined_file, 'r') as f:
            combined_results = json.load(f)
    
    # Load verification results
    verification_file = os.path.join(temp_base, 'verification_results.json')
    verification_result = {}
    if os.path.exists(verification_file):
        with open(verification_file, 'r') as f:
            verification_result = json.load(f)
    
    # Collect generated files
    files_generated = []
    for file_info in combined_results.get('generated_files', []):
        if isinstance(file_info, dict) and 'path' in file_info:
            files_generated.append(file_info['path'])
    
    # Also check for the main expected files
    expected_files = [
        os.path.join(temp_dir, 'dipeo/models/__generated_models__.py'),
        os.path.join(temp_dir, 'dipeo/models/__generated_conversions__.py'),
        os.path.join(temp_dir, 'dipeo/models/src/generated/zod_schemas.ts')
    ]
    
    for file_path in expected_files:
        if os.path.exists(file_path) and file_path not in files_generated:
            files_generated.append(file_path)
    
    # Build result object
    result = {
        'success': len(files_generated) > 0 and len(verification_result.get('errors', [])) == 0,
        'files_generated': files_generated,
        'message': f'Generated {len(files_generated)} domain model files',
        'timestamp': datetime.now().isoformat(),
        'execution_id': execution_id,
        'verification': verification_result,
        'file_count': combined_results.get('file_count', 0)
    }
    
    # Save to file
    output_file = os.path.join(output_dir, 'domain_models_result.json')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"[save_domain_model_results] Saved results to: {output_file}")
    print(f"[save_domain_model_results] Generated {len(files_generated)} files")
    
    return {
        'saved_to': output_file,
        'files_count': len(files_generated),
        'success': result['success']
    }


def save_node_ui_results(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Save node UI generation results to file"""
    # Get execution context
    execution_id = inputs.get('execution_id', 'unknown')
    output_dir = inputs.get('output_dir', 'logs/codegen/runs/unknown')
    node_spec_path = inputs.get('node_spec_path', '')
    
    # Get results from generation process
    registry_updates = inputs.get('registry_updates', {})
    registration_result = inputs.get('registration_result', {})
    
    # Extract generated files
    files_generated = registry_updates.get('files_generated', [])
    
    # Build result object
    result = {
        'success': registration_result.get('success', False),
        'files_generated': files_generated,
        'message': registration_result.get('message', f'Generated {len(files_generated)} node UI files'),
        'timestamp': datetime.now().isoformat(),
        'execution_id': execution_id,
        'node_spec': node_spec_path,
        'registry_updates': registry_updates,
        'registration': registration_result
    }
    
    # Save to file
    output_file = os.path.join(output_dir, 'node_ui_result.json')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    return {
        'saved_to': output_file,
        'files_count': len(files_generated)
    }