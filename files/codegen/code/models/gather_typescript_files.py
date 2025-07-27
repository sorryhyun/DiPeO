"""Gather TypeScript model files for batch parsing."""
import os
from pathlib import Path
from typing import Dict, Any


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
    
    file_paths = [
        'dipeo/models/src/diagram.ts',
        'dipeo/models/src/execution.ts',
        'dipeo/models/src/conversation.ts',
        'dipeo/models/src/node-specifications.ts',
        'dipeo/models/src/diagram-utils.ts',
        'dipeo/models/src/service-utils.ts',
        'dipeo/models/src/integration.ts',
        'dipeo/models/src/node-data/index.ts',
        'dipeo/models/src/conversions.ts',
        'dipeo/models/src/codegen-mappings.ts',
        'dipeo/models/src/enums.ts'
    ]
    
    # Add all individual node data files
    node_data_files = [
        'dipeo/models/src/node-data/start.data.ts',
        'dipeo/models/src/node-data/condition.data.ts',
        'dipeo/models/src/node-data/person-job.data.ts',
        'dipeo/models/src/node-data/code-job.data.ts',
        'dipeo/models/src/node-data/api-job.data.ts',
        'dipeo/models/src/node-data/endpoint.data.ts',
        'dipeo/models/src/node-data/db.data.ts',
        'dipeo/models/src/node-data/user-response.data.ts',
        'dipeo/models/src/node-data/notion.data.ts',
        'dipeo/models/src/node-data/person-batch-job.data.ts',
        'dipeo/models/src/node-data/hook.data.ts',
        'dipeo/models/src/node-data/template-job.data.ts',
        'dipeo/models/src/node-data/json-schema-validator.data.ts',
        'dipeo/models/src/node-data/typescript-ast.data.ts',
        'dipeo/models/src/node-data/sub-diagram.data.ts'
    ]
    
    file_paths.extend(node_data_files)
    
    # Map file paths to simpler keys for the cache
    file_mapping = {
        'dipeo/models/src/diagram.ts': 'diagram',
        'dipeo/models/src/execution.ts': 'execution',
        'dipeo/models/src/conversation.ts': 'conversation',
        'dipeo/models/src/node-specifications.ts': 'node_specifications',
        'dipeo/models/src/diagram-utils.ts': 'diagram_utils',
        'dipeo/models/src/service-utils.ts': 'service_utils',
        'dipeo/models/src/integration.ts': 'integration',
        'dipeo/models/src/node-data/index.ts': 'node_data',
        'dipeo/models/src/conversions.ts': 'conversions',
        'dipeo/models/src/codegen-mappings.ts': 'codegen_mappings',
        'dipeo/models/src/enums.ts': 'enums'
    }
    
    # Add mappings for individual node data files
    for node_file in node_data_files:
        # Extract the base name without extension
        # e.g., 'dipeo/models/src/node-data/start.data.ts' -> 'start_data'
        base_name = node_file.split('/')[-1].replace('.data.ts', '_data')
        file_mapping[node_file] = base_name
    
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
    
    return {
        'sources': sources,
        'file_mapping': file_mapping,  
        'file_count': len(sources)
    }


# Keep backward compatibility
def gather_typescript_files() -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    return main({})