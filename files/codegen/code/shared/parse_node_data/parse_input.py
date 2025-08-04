def main(inputs):
    """Parse input to extract node type from various input formats."""
    node_type = None
    
    # Check if we have a default value in inputs (batch processing case)
    if 'default' in inputs:
        default_data = inputs['default']
        if isinstance(default_data, dict) and 'node_type' in default_data:
            node_type = default_data['node_type']
        elif isinstance(default_data, str):
            node_type = default_data
    
    # If not found, try direct node_type in inputs
    if not node_type and 'node_type' in inputs:
        node_type = inputs['node_type']
    
    if not node_type:
        # Debug output to understand what we're receiving
        debug_info = {
            'inputs': inputs,
            'default_value': inputs.get('default', 'NOT_FOUND')
        }
        raise ValueError(f"node_type not provided in input. Debug: {debug_info}")
    
    # Convert underscore to hyphen for cache filename
    cache_filename = node_type.replace('_', '-') + '_data'
    
    return {"node_type": node_type, "cache_filename": cache_filename}