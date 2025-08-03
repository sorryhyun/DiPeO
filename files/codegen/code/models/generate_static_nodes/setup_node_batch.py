"""Setup batch processing for node data parsing."""
import json
import os
import shutil
from typing import Any, Dict


def setup_node_batch(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Prepare batch processing setup by parsing manifest and creating temp directory.
    
    Args:
        inputs: Dictionary containing manifest data
        
    Returns:
        Dictionary with items array for batch processing and metadata
    """
    
    # When no label is specified, db node might wrap in 'default'
    if 'default' in inputs and len(inputs) == 1:
        manifest_data = inputs['default']
    else:
        manifest_data = inputs
        
    if isinstance(manifest_data, str):
        manifest_data = json.loads(manifest_data)
    
    # Get node types from manifest
    node_types = manifest_data.get('nodes', [])
    
    if not node_types:
        raise ValueError("No node types found in manifest")
    
    # Create temp directory for storing results
    temp_dir = '.temp/codegen/node_data'
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    os.makedirs(temp_dir, exist_ok=True)
    
    # Create array of inputs for batch processing
    # Match the pattern used in working batch examples
    items = [{'node_type': node_type} for node_type in node_types]
    
    
    result = {
        'items': items,
        'node_types': node_types,
        'temp_dir': temp_dir
    }
    
    return result