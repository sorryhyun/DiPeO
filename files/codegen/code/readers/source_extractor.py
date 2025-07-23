"""Source code extractor for TypeScript AST parser."""

from typing import Dict, Any


def extract_source(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Extract source code from inputs for TypeScript AST parser."""
    # Debug: print the structure of inputs
    print(f"extract_source received inputs structure: {list(inputs.keys())}")
    
    # DiPeO passes the entire output from previous node
    # When content_type is 'object', the data is directly in inputs
    source = inputs.get('source', '')
    files = inputs.get('files', [])
    file_count = inputs.get('file_count', 0)
    
    if not source and 'value' in inputs and isinstance(inputs['value'], dict):
        # Sometimes DiPeO wraps the output in a 'value' key
        source = inputs['value'].get('source', '')
        files = inputs['value'].get('files', files)
        file_count = inputs['value'].get('file_count', file_count)
    
    print(f"Extracted source code, length: {len(source)}")
    print(f"File count: {file_count}")
    
    # The TypeScript AST parser expects just 'source' as input
    # Return only what the parser needs
    return {'source': source}