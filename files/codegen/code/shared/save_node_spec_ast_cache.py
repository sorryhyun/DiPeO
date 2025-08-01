"""Save parsed node spec AST data to cache directory."""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for saving node spec AST cache.
    
    Args:
        inputs: Dictionary containing labeled inputs from multiple nodes
        
    Returns:
        Dictionary containing:
        - status: Success status
        - cache_dir: Path to cache directory
        - cache_files: Dict mapping node types to cache file paths
        - metadata: Cache metadata including counts and timestamp
    """
    # Get the base directory from environment or use current directory
    base_dir = Path(os.environ.get('DIPEO_BASE_DIR', os.getcwd()))
    
    # Extract parsed_results from the Batch Parse Node Specs node
    parsed_data = inputs.get('parsed_results', {})
    if isinstance(parsed_data, dict) and 'parsed_results' in parsed_data:
        parsed_results = parsed_data['parsed_results']
        metadata = parsed_data.get('metadata', {})
    else:
        parsed_results = parsed_data
        metadata = inputs.get('metadata', {})
    
    # Extract file_mapping from the Gather Node Spec Files node
    file_mapping_data = inputs.get('file_mapping', {})
    if isinstance(file_mapping_data, dict) and 'file_mapping' in file_mapping_data:
        file_mapping = file_mapping_data['file_mapping']
    else:
        file_mapping = file_mapping_data
    
    # Create cache directory at project root
    cache_dir = base_dir / '.temp'
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Track cache files and statistics
    cache_files = {}
    total_specs = 0
    total_constants = 0
    
    # Save each node spec AST
    for node_type, ast_data in parsed_results.items():
        if not isinstance(ast_data, dict):
            print(f"Warning: Invalid AST data for {node_type}")
            continue
        
        # Count constants (node specs are exported as constants)
        constants = ast_data.get('constants', [])
        total_constants += len(constants)
        
        # Save individual node spec AST
        cache_file = cache_dir / f'node_spec_{node_type}_ast.json'
        cache_files[node_type] = str(cache_file)
        
        with open(cache_file, 'w') as f:
            json.dump(ast_data, f, indent=2)
        
        total_specs += 1
        
        # Find the spec constant for this node type
        spec_name = f"{node_type.replace('_', ' ').title().replace(' ', '')}Spec"
        spec_name = spec_name[0].lower() + spec_name[1:]  # camelCase
        
        spec_found = any(c.get('name') == spec_name for c in constants)
        # Spec validation done silently
    
    # Also save a consolidated cache file with all node specs
    consolidated_cache = cache_dir / 'all_node_specs_ast.json'
    with open(consolidated_cache, 'w') as f:
        json.dump({
            'node_specs': parsed_results,
            'metadata': {
                'total_specs': total_specs,
                'total_constants': total_constants,
                'timestamp': datetime.now().isoformat()
            }
        }, f, indent=2)
    
    # Save metadata
    cache_metadata = {
        'total_node_specs': total_specs,
        'total_constants': total_constants,
        'timestamp': datetime.now().isoformat(),
        'cache_dir': str(cache_dir),
        'cache_files': cache_files,
        'consolidated_cache': str(consolidated_cache),
        'batch_processing_time_ms': metadata.get('processingTimeMs', 0)
    }
    
    metadata_file = cache_dir / 'node_spec_metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(cache_metadata, f, indent=2)
    
    print(f"Cached {total_specs} node specs - done!")
    
    return {
        'status': 'success',
        'cache_dir': str(cache_dir),
        'cache_files': cache_files,
        'metadata': cache_metadata
    }