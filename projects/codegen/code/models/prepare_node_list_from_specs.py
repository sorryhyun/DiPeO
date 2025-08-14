"""Prepare node list from dynamically loaded spec files."""
import json
from typing import Any, Dict, List


def prepare_node_list_from_specs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract node types from all loaded spec AST files and prepare for batch processing.
    
    Args:
        inputs: Dictionary containing loaded AST data from glob pattern
        
    Returns:
        Dictionary with items array for batch processing
    """
    
    node_types = []
    
    # Handle case where db node passes data as 'default'
    # Also handle when code_job adds 'inputs' and 'node_id' keys
    if 'default' in inputs:
        # The actual data is in the 'default' key
        actual_data = inputs['default']
        # Check if this looks like the spec files (should be a dict with file paths as keys)
        if isinstance(actual_data, dict) and any(k.endswith('.spec.ts.json') for k in actual_data.keys()):
            inputs = actual_data
    
    # Process each spec file
    for filename, ast_data in inputs.items():
        if filename == 'default' or not filename.endswith('.spec.ts.json'):
            continue
        
        # Extract node type from filename (e.g., "api-job.spec.ts.json" -> "api-job")
        # Keep the hyphen format to match the actual file names
        base_filename = filename.split('/')[-1]
        node_type = base_filename.replace('.spec.ts.json', '')
        
        # Verify the spec file contains valid node specification
        if isinstance(ast_data, dict):
            # Check if it has the expected structure
            constants = ast_data.get('constants', [])
            for const in constants:
                # Check for both 'Spec' and 'spec' to handle camelCase naming
                name = const.get('name', '')
                if name.endswith('Spec') or name.endswith('spec'):
                    # Found a valid node spec
                    node_types.append(node_type)
                    break
    
    if not node_types:
        raise ValueError("No node types found in spec files")
    
    # Verbose logging removed - generating backend files for {len(node_types)} nodes
    # Uncomment below for debugging:
    # print(f"Generating backend files for {len(node_types)} nodes from TypeScript specifications:")
    # for nt in sorted(node_types):
    #     print(f"  - {nt}")
    
    # Create array of inputs for batch processing
    # Return directly with 'items' key for batch processing
    result = {
        'items': [{'node_spec_path': node_type} for node_type in sorted(node_types)]
    }
    
    return result