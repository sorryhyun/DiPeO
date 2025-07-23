"""Extract source code from typescript reader output."""

def extract_source_for_ast(inputs):
    """Extract the source field from typescript reader output for AST parsing."""
    print(f"[extract_source_for_ast] Received inputs keys: {list(inputs.keys())}")
    
    # Check various locations where source might be
    source = None
    
    # Direct source key
    if 'source' in inputs:
        source = inputs['source']
        print(f"[extract_source_for_ast] Found source in direct key")
    # In default dict
    elif 'default' in inputs and isinstance(inputs['default'], dict):
        source = inputs['default'].get('source', '')
        print(f"[extract_source_for_ast] Found source in default dict")
        print(f"[extract_source_for_ast] Default dict keys: {list(inputs['default'].keys())}")
    # In value dict  
    elif 'value' in inputs and isinstance(inputs['value'], dict):
        source = inputs['value'].get('source', '')
        print(f"[extract_source_for_ast] Found source in value dict")
    
    if source:
        print(f"[extract_source_for_ast] Found source with length: {len(source)}")
    else:
        print(f"[extract_source_for_ast] No source found")
        print(f"[extract_source_for_ast] Input structure: {inputs}")
        if 'default' in inputs and isinstance(inputs['default'], dict):
            print(f"[extract_source_for_ast] Default dict contents: {inputs['default']}")
    
    # Return in the format expected by typescript_ast node
    return {
        'source': source or '',
        'default': {'source': source or ''}
    }