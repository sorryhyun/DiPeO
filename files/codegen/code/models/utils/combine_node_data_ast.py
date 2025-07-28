import json
import os
from pathlib import Path


def main(inputs):
    # Get base directory
    base_dir = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
    
    # Read all node data AST files from cache
    cache_dir = base_dir / '.temp'
    
    # Combine all interfaces, types, and enums from node data files
    all_interfaces = []
    all_types = []
    all_enums = []
    
    # List of node data cache files
    node_data_files = [
        'start_data_ast.json', 'condition_data_ast.json', 'person-job_data_ast.json',
        'code-job_data_ast.json', 'api-job_data_ast.json', 'endpoint_data_ast.json',
        'db_data_ast.json', 'user-response_data_ast.json', 'notion_data_ast.json',
        'person-batch-job_data_ast.json', 'hook_data_ast.json', 'template-job_data_ast.json',
        'json-schema-validator_data_ast.json', 'typescript-ast_data_ast.json', 'sub-diagram_data_ast.json'
    ]
    
    print(f"Looking for cache files in: {cache_dir}")
    
    for filename in node_data_files:
        file_path = cache_dir / filename
        if file_path.exists():
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    all_interfaces.extend(data.get('interfaces', []))
                    all_types.extend(data.get('types', []))
                    all_enums.extend(data.get('enums', []))
                    print(f"  Loaded {filename}: {len(data.get('interfaces', []))} interfaces")
            except Exception as e:
                print(f"  Error reading {filename}: {e}")
        else:
            print(f"  File not found: {filename}")
    
    print(f"Combined node data: {len(all_interfaces)} interfaces, {len(all_types)} types, {len(all_enums)} enums")
    
    result = {
        'interfaces': all_interfaces,
        'types': all_types,
        'enums': all_enums
    }
    
    return result