"""Read batch processing results from temporary files."""
import json
import os
import shutil
from typing import Any, Dict, List


def read_batch_results(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Read all temporary files created by batch processing.
    
    Args:
        inputs: Dictionary containing batch_info with temp_dir and node_types
        
    Returns:
        Dictionary with parsed_nodes array and count
    """
    # Get batch info
    batch_info = inputs.get('batch_info', {})
    temp_dir = batch_info.get('temp_dir', '.temp/codegen/node_data')
    node_types = batch_info.get('node_types', [])
    
    # Read all temp files
    parsed_nodes: List[Dict[str, Any]] = []
    
    for node_type in node_types:
        temp_file = os.path.join(temp_dir, f"{node_type}.json")
        if os.path.exists(temp_file):
            try:
                with open(temp_file, 'r') as f:
                    data = json.load(f)
                parsed_nodes.append(data)
            except Exception as e:
                pass  # Skip failed files silently
    
    # Clean up temp directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    result = {
        'parsed_nodes': parsed_nodes,
        'count': len(parsed_nodes)
    }
    
    return result