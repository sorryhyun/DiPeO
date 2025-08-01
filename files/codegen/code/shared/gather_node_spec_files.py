"""Gather all TypeScript node specification files for batch processing."""

import os
from pathlib import Path
from typing import Dict, List, Any


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Gather all node spec files based on discovered specs.
    
    Args:
        inputs: Contains 'discovered_specs' with node names from discovery
        
    Returns:
        Dict with 'sources' (list of file paths) and 'file_mapping' (dict mapping node type to file path)
    """
    discovered = inputs.get('discovered_specs', {})
    
    # Get node names from discovery
    node_types = discovered.get('node_names', [])
    
    if not node_types:
        raise ValueError("No node types found from discovery")
    
    # Base directory for node specs
    base_dir = Path(os.environ.get('DIPEO_BASE_DIR', os.getcwd())) / "dipeo/models/src/node-specs"
    
    sources = []
    file_mapping = {}
    missing_files = []
    
    for node_type in node_types:
        # Convert underscore to hyphen for filename
        node_type_filename = node_type.replace('_', '-')
        file_path = base_dir / f"{node_type_filename}.spec.ts"
        
        if file_path.exists():
            sources.append(str(file_path))
            file_mapping[node_type] = str(file_path)
        else:
            # Try with underscores as well
            file_path = base_dir / f"{node_type}.spec.ts"
            if file_path.exists():
                sources.append(str(file_path))
                file_mapping[node_type] = str(file_path)
            else:
                missing_files.append(node_type)
    
    if missing_files:
        print(f"Warning: Missing spec files for node types: {missing_files}")
    
    print(f"Found {len(sources)} specs")
    
    return {
        'sources': sources,
        'file_mapping': file_mapping
    }