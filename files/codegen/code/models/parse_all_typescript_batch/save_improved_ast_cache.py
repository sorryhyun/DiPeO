"""Save improved AST cache from typescript_ast batch processing."""

import json
import os
from pathlib import Path
from typing import Dict, Any, List


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Save batch AST parsing results to cache files.
    
    Args:
        inputs: Dictionary containing:
            - results: Batch processing results from sub_diagram
            - file_mapping: Mapping of file paths to keys
    
    Returns:
        Dictionary with cache save status.
    """
    batch_results = inputs.get('results', [])
    file_mapping = inputs.get('file_mapping', {})
    
    # Ensure .temp directory exists
    temp_dir = Path('.temp')
    temp_dir.mkdir(exist_ok=True)
    
    # Process each result
    saved_count = 0
    failed_count = 0
    total_interfaces = 0
    total_types = 0
    total_enums = 0
    
    for result in batch_results:
        if isinstance(result, dict):
            key = result.get('key', '')
            file_path = result.get('file_path', '')
            ast_data = result.get('ast', {})
            
            if ast_data:
                # Determine cache filename
                cache_key = key or Path(file_path).stem.replace('.', '_')
                cache_path = temp_dir / f"{cache_key}_ast.json"
                
                try:
                    # Save the AST data
                    with open(cache_path, 'w') as f:
                        json.dump(ast_data, f, indent=2)
                    
                    saved_count += 1
                    
                    # Count definitions
                    total_interfaces += len(ast_data.get('interfaces', []))
                    total_types += len(ast_data.get('types', []))
                    total_enums += len(ast_data.get('enums', []))
                    
                    print(f"[AST Cache] Saved {cache_key} to {cache_path}")
                    
                except Exception as e:
                    print(f"[AST Cache] Failed to save {cache_key}: {str(e)}")
                    failed_count += 1
            else:
                print(f"[AST Cache] No AST data for {key or file_path}")
                failed_count += 1
    
    # Create a summary file
    summary = {
        'total_files': len(batch_results),
        'saved_count': saved_count,
        'failed_count': failed_count,
        'total_interfaces': total_interfaces,
        'total_types': total_types,
        'total_enums': total_enums,
        'file_mapping': file_mapping
    }
    
    summary_path = temp_dir / 'ast_cache_summary.json'
    with open(summary_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"\n=== AST Cache Save Complete ===")
    print(f"Total files processed: {len(batch_results)}")
    print(f"Successfully cached: {saved_count}")
    print(f"Failed: {failed_count}")
    print(f"Total definitions: {total_interfaces} interfaces, {total_types} types, {total_enums} enums")
    print(f"Summary saved to: {summary_path}")
    
    return {
        'cache_status': 'success' if failed_count == 0 else 'partial',
        'summary': summary
    }