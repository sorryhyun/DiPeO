"""Extract source code from typescript reader output."""

def extract_source_for_ast(inputs):
    """Extract the source field from typescript reader output for AST parsing."""
    print(f"[extract_source_for_ast] Received inputs keys: {list(inputs.keys())}")
    
    # Check various locations where source might be
    source = None
    
    # Direct source key
    if 'source' in inputs:
        source = inputs['source']
    # In default dict
    elif 'default' in inputs and isinstance(inputs['default'], dict):
        source = inputs['default'].get('source', '')
    # In value dict  
    elif 'value' in inputs and isinstance(inputs['value'], dict):
        source = inputs['value'].get('source', '')
    
    if source:
        print(f"[extract_source_for_ast] Found source with length: {len(source)}")
    else:
        print(f"[extract_source_for_ast] No source found")
        print(f"[extract_source_for_ast] Input structure: {inputs}")
    
    # Return in the format expected by typescript_ast node
    return {
        'source': source or '',
        'default': {'source': source or ''}
    }