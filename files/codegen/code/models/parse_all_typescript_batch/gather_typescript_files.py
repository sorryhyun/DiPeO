"""Gather TypeScript model files for batch parsing."""
import os
from pathlib import Path
from typing import Dict, Any
import glob


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for gathering TypeScript files.
    
    Args:
        inputs: Input data from the diagram execution
        
    Returns:
        Dictionary containing:
        - sources: Dict mapping file paths to their source content
        - file_mapping: Dict mapping file paths to simplified keys
        - file_count: Number of files gathered
    """
    base_dir = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
    
    # Core files that should always be included
    core_files = [
        'dipeo/models/src/diagram.ts',
        'dipeo/models/src/execution.ts',
        'dipeo/models/src/conversation.ts',
        'dipeo/models/src/node-specs/node-specifications.ts',
        'dipeo/models/src/diagram-utils.ts',
        'dipeo/models/src/service-utils.ts',
        'dipeo/models/src/integration.ts',
        'dipeo/models/src/node-data/index.ts',
        'dipeo/models/src/conversions.ts',
        'dipeo/models/src/codegen-mappings.ts',
        'dipeo/models/src/enums.ts'
    ]
    
    # Auto-discover all node data files
    node_data_pattern = str(base_dir / 'dipeo/models/src/node-data/*.data.ts')
    node_data_files = [
        str(Path(f).relative_to(base_dir)) 
        for f in glob.glob(node_data_pattern)
    ]
    
    # Auto-discover all node spec files (excluding index.ts and node-specifications.ts)
    node_spec_pattern = str(base_dir / 'dipeo/models/src/node-specs/*.spec.ts')
    node_spec_files = [
        str(Path(f).relative_to(base_dir)) 
        for f in glob.glob(node_spec_pattern)
    ]
    
    # Combine all files
    file_paths = core_files + node_data_files + node_spec_files
    
    # Map file paths to simpler keys for the cache
    file_mapping = {
        'dipeo/models/src/diagram.ts': 'diagram',
        'dipeo/models/src/execution.ts': 'execution',
        'dipeo/models/src/conversation.ts': 'conversation',
        'dipeo/models/src/node-specs/node-specifications.ts': 'node_specifications',
        'dipeo/models/src/diagram-utils.ts': 'diagram_utils',
        'dipeo/models/src/service-utils.ts': 'service_utils',
        'dipeo/models/src/integration.ts': 'integration',
        'dipeo/models/src/node-data/index.ts': 'node_data',
        'dipeo/models/src/conversions.ts': 'conversions',
        'dipeo/models/src/codegen-mappings.ts': 'codegen_mappings',
        'dipeo/models/src/enums.ts': 'enums'
    }
    
    # Add mappings for auto-discovered node data files
    for node_file in node_data_files:
        # Extract the base name without extension
        # e.g., 'dipeo/models/src/node-data/start.data.ts' -> 'start_data'
        base_name = Path(node_file).stem.replace('.data', '_data')
        file_mapping[node_file] = base_name
    
    # Add mappings for auto-discovered node spec files
    for spec_file in node_spec_files:
        # e.g., 'dipeo/models/src/node-specs/start.spec.ts' -> 'start_spec'
        base_name = Path(spec_file).stem.replace('.spec', '_spec')
        file_mapping[spec_file] = base_name
    
    # Read all files
    sources = {}
    for file_path in file_paths:
        full_path = base_dir / file_path
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                sources[file_path] = f.read()
        except Exception as e:
            print(f"Error reading {full_path}: {e}")
    
    print(f"Gathered {len(sources)} TypeScript files for batch parsing")
    print(f"  - Core files: {len(core_files)}")
    print(f"  - Auto-discovered node data files: {len(node_data_files)}")
    print(f"  - Auto-discovered node spec files: {len(node_spec_files)}")
    
    result = {
        'sources': sources,
        'file_mapping': file_mapping,  
        'file_count': len(sources)
    }
    
    return result


# Keep backward compatibility
def gather_typescript_files() -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    return main({})