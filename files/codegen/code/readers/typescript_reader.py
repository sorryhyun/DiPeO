"""TypeScript file reader for code generation."""

import os
from typing import Dict, Any


def read_typescript_files(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Read content of TypeScript files and combine them for parsing."""
    print(f"read_typescript_files received inputs: {list(inputs.keys())}")
    
    # DiPeO may pass data under different keys
    files = []
    if 'file_list' in inputs and isinstance(inputs['file_list'], dict):
        # From labeled connection
        files = inputs['file_list'].get('typescript_files', [])
    elif 'typescript_files' in inputs:
        files = inputs['typescript_files']
    elif 'default' in inputs:
        files = inputs['default'].get('typescript_files', [])
    
    print(f"Processing {len(files)} TypeScript files")
    file_contents = []
    
    for file_path in files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                file_contents.append({
                    'path': file_path,
                    'content': content,
                    'filename': os.path.basename(file_path)
                })
                print(f"Read {file_path}: {len(content)} characters")
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            continue
    
    # Combine all content for parsing
    combined_source = '\n\n// --- File Separator ---\n\n'.join(
        [f"// File: {fc['filename']}\n{fc['content']}" for fc in file_contents]
    )
    
    result = {
        'source': combined_source,
        'files': file_contents,
        'file_count': len(file_contents)
    }
    
    print(f"Returning combined source of length: {len(combined_source)}")
    print(f"Result keys: {list(result.keys())}")
    
    # For DiPeO handle-based data passing, return with both direct keys and default
    result['default'] = result.copy()
    
    return result