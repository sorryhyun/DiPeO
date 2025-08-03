"""Batch parse TypeScript node spec files using the AST extractor."""

import json
import subprocess
import tempfile
import os
from pathlib import Path
from typing import Dict, Any


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for batch TypeScript node spec parsing.
    
    Args:
        inputs: Dictionary containing 'sources' labeled input
        
    Returns:
        Dictionary containing:
        - parsed_results: Mapped parse results by node type
        - metadata: Batch processing metadata
    """
    # Extract sources and file mapping from input
    sources_data = inputs.get('sources', {})
    
    if isinstance(sources_data, dict):
        sources = sources_data.get('sources', [])
        file_mapping = sources_data.get('file_mapping', {})
    else:
        sources = sources_data
        file_mapping = {}
    
    if not sources:
        raise ValueError("No sources provided for batch parsing")
    
    # Prepare batch input and save to temp file
    batch_input = {'sources': sources}
    
    # Create temporary file for batch input
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as tmp_file:
        json.dump(batch_input, tmp_file)
        tmp_file_path = tmp_file.name
    
    # Run the TypeScript parser in batch mode
    project_root = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))
    parser_script = project_root / 'dipeo' / 'infra' / 'parsers' / 'typescript' / 'ts_ast_extractor.ts'
    
    cmd = [
        'pnpm', 'tsx', str(parser_script),
        f'--batch-input={tmp_file_path}',
        '--patterns=const',  # Node specs use export const
        '--include-jsdoc',
        '--mode=module'
    ]
    
    print(f"Executing batch TypeScript parsing for {len(sources)} node spec files...")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=60
        )
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        if result.returncode != 0:
            raise RuntimeError(f"Parser failed: {result.stderr}")
        
        # Parse the batch result
        batch_result = json.loads(result.stdout)
        
        # Map results by node type
        mapped_results = {}
        
        # Create a list-based mapping since results are indexed numerically
        source_list = sources if isinstance(sources, list) else sources.get('sources', [])
        
        # Invert the file_mapping to get node_type from file_path
        file_to_node_type = {v: k for k, v in file_mapping.items()}
        
        # Debug: print first result to see structure
        results = batch_result.get('results', {})
        
        # Handle both numeric indices and file paths
        for key, parse_result in results.items():
            # The parser returns file paths as keys when using --batch-input
            if key in file_to_node_type:
                # Direct file path match
                node_type = file_to_node_type[key]
                mapped_results[node_type] = parse_result
            elif key.isdigit():
                # Numeric index - use the source list
                index = int(key)
                if index < len(source_list):
                    file_path = source_list[index]
                    node_type = file_to_node_type.get(file_path)
                    if node_type:
                        mapped_results[node_type] = parse_result
                    else:
                        # Extract node type from file path
                        basename = os.path.basename(file_path)
                        node_name = basename.replace('.spec.ts', '').replace('-', '_')
                        mapped_results[node_name] = parse_result
            else:
                # Try to extract node type from the key itself
                basename = os.path.basename(key)
                node_name = basename.replace('.spec.ts', '').replace('-', '_')
                if node_name in file_mapping:
                    mapped_results[node_name] = parse_result
                else:
                    print(f"Warning: Unable to map result key '{key}' to a node type")
        
        # Log performance metrics
        if 'metadata' in batch_result:
            meta = batch_result['metadata']
            print(f"\n=== Node Spec Batch Parsing Complete ===")
            print(f"Total files: {meta['totalFiles']}")
            print(f"Successful: {meta['successCount']}")
            print(f"Failed: {meta['failureCount']}")
            print(f"Processing time: {meta['processingTimeMs']}ms")
        
        return {
            'parsed_results': mapped_results,
            'metadata': batch_result.get('metadata', {})
        }
        
    except subprocess.TimeoutExpired:
        # Clean up temp file if it exists
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        raise RuntimeError("Batch TypeScript parsing timed out after 60 seconds")
    except json.JSONDecodeError as e:
        # Clean up temp file if it exists
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        raise RuntimeError(f"Failed to parse batch output: {str(e)}")
    except Exception as e:
        # Clean up temp file if it exists
        if 'tmp_file_path' in locals():
            try:
                os.unlink(tmp_file_path)
            except:
                pass
        raise