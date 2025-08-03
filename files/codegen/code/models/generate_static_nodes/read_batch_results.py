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
    
    print(f"[read_batch_results] Called with inputs keys: {list(inputs.keys())}")
    
    # Handle different input formats
    # When coming from batch processing, might be wrapped in 'default'
    if 'default' in inputs and 'batch_info' not in inputs:
        # This is from the batch sub-diagram output
        batch_output = inputs['default']
        # Still need batch_info from the other connection
        batch_info = {}
        temp_dir = '.temp/codegen/node_data'
        node_types = []
    else:
        # Get batch info from labeled connection
        batch_info = inputs.get('batch_info', {})
        temp_dir = batch_info.get('temp_dir', '.temp/codegen/node_data')
        node_types = batch_info.get('node_types', [])
    
    # Read all temp files
    parsed_nodes: List[Dict[str, Any]] = []
    
    
    # If node_types is empty, scan the directory for JSON files
    if not node_types and os.path.exists(temp_dir):
        json_files = [f for f in os.listdir(temp_dir) if f.endswith('.json')]
        node_types = [f[:-5] for f in json_files]  # Remove .json extension
        print(f"[read_batch_results] Found {len(json_files)} JSON files in {temp_dir}")
    else:
        print(f"[read_batch_results] Using {len(node_types)} node types from batch_info")
    
    
    for node_type in node_types:
        temp_file = os.path.join(temp_dir, f"{node_type}.json")
        if os.path.exists(temp_file):
            try:
                with open(temp_file, 'r') as f:
                    data = json.load(f)
                parsed_nodes.append(data)
            except Exception as e:
                pass  # Skip failed files silently
        else:
            # File doesn't exist, skip it
            pass
    
    # Clean up temp directory
    if os.path.exists(temp_dir):
        shutil.rmtree(temp_dir)
    
    result = {
        'parsed_nodes': parsed_nodes,
        'count': len(parsed_nodes)
    }
    
    print(f"[read_batch_results] Returning {len(parsed_nodes)} parsed nodes")
    
    return result