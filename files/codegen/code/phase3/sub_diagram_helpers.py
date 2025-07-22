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
    
    # Collect results from the generation process
    files_generated = []
    
    # These would come from actual generation steps
    # For now, using placeholder data
    verification_result = inputs.get('verification_result', {})
    
    # In real implementation, collect actual generated files
    # For phase 3, we expect these files:
    expected_files = [
        'dipeo/models/__generated_models__.py',
        'dipeo/models/__generated_conversions__.py', 
        'dipeo/core/static/generated_nodes.py',
        'apps/web/src/graphql/__generated__/types.ts'
    ]
    
    # Check which files actually exist
    for file_path in expected_files:
        if os.path.exists(file_path):
            files_generated.append(file_path)
    
    # Build result object
    result = {
        'success': len(files_generated) > 0,
        'files_generated': files_generated,
        'message': f'Generated {len(files_generated)} domain model files',
        'timestamp': datetime.now().isoformat(),
        'execution_id': execution_id,
        'verification': verification_result
    }
    
    # Save to file
    output_file = os.path.join(output_dir, 'domain_models_result.json')
    os.makedirs(output_dir, exist_ok=True)
    
    with open(output_file, 'w') as f:
        json.dump(result, f, indent=2)
    
    return {
        'saved_to': output_file,
        'files_count': len(files_generated)
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