"""Save parsed AST data to cache directory."""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for saving AST cache.
    
    Args:
        inputs: Dictionary containing labeled inputs from multiple nodes
        
    Returns:
        Dictionary containing:
        - status: Success status
        - cache_dir: Path to cache directory
        - metadata: Cache metadata including counts and timestamp
    """
    # Get the base directory from environment or use current directory
    base_dir = Path(os.environ.get('DIPEO_BASE_DIR', os.getcwd()))
    # Extract parsed_results from the Batch Parse TypeScript node
    parsed_data = inputs.get('parsed_results', {})
    if isinstance(parsed_data, dict) and 'parsed_results' in parsed_data:
        parsed_results = parsed_data['parsed_results']
        metadata = parsed_data.get('metadata', {})
    else:
        parsed_results = parsed_data
        metadata = inputs.get('metadata', {})
    
    # Extract sources and file_mapping from the Gather File Paths node
    sources_data = inputs.get('sources', {})
    if isinstance(sources_data, dict) and 'sources' in sources_data:
        sources = sources_data['sources']
        file_mapping = sources_data.get('file_mapping', {})
    else:
        sources = sources_data
        file_mapping_data = inputs.get('file_mapping', {})
        if isinstance(file_mapping_data, dict) and 'file_mapping' in file_mapping_data:
            file_mapping = file_mapping_data['file_mapping']
        else:
            file_mapping = file_mapping_data
    
    # Create cache directory at project root
    cache_dir = base_dir / '.temp'
    cache_dir.mkdir(parents=True, exist_ok=True)
    
    # Calculate totals
    total_interfaces = 0
    total_types = 0
    total_enums = 0
    total_consts = 0
    
    # Save each AST file
    for file_path, key in file_mapping.items():
        # The parsed_results are keyed by the mapped key, not the original file_path
        if not isinstance(parsed_results, dict) or key not in parsed_results:
            print(f"Warning: No parsed result for {key} (looking for path: {file_path})")
            continue
        
        parse_result = parsed_results[key]
        ast_data = {
            'interfaces': parse_result.get('interfaces', []),
            'types': parse_result.get('types', []),
            'enums': parse_result.get('enums', []),
            'constants': parse_result.get('constants', [])
        }
        
        # Count definitions
        total_interfaces += len(ast_data['interfaces'])
        total_types += len(ast_data['types'])
        total_enums += len(ast_data['enums'])
        total_consts += len(ast_data['constants'])
        
        # Save AST data
        ast_file = cache_dir / f'{key}_ast.json'
        with open(ast_file, 'w') as f:
            json.dump(ast_data, f, indent=2)
        
        # Save source code
        if file_path in sources:
            source_file = cache_dir / f'{key}_source.ts'
            with open(source_file, 'w') as f:
                f.write(sources[file_path])
    
    # Save metadata
    cache_metadata = {
        'total_files': len(parsed_results),
        'total_interfaces': total_interfaces,
        'total_types': total_types,
        'total_enums': total_enums,
        'total_constants': total_consts,
        'timestamp': datetime.now().isoformat(),
        'cache_dir': str(cache_dir),
        'batch_processing_time_ms': metadata.get('processingTimeMs', 0)
    }
    
    metadata_file = cache_dir / 'metadata.json'
    with open(metadata_file, 'w') as f:
        json.dump(cache_metadata, f, indent=2)
    
    print(f"Parsed {len(parsed_results)} files - {total_interfaces} interfaces, {total_types} types, {total_enums} enums, {total_consts} constants - done!")
    
    return {
        'status': 'success',
        'cache_dir': str(cache_dir),
        'metadata': cache_metadata
    }


# Keep backward compatibility
def save_ast_cache(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    return main(inputs)