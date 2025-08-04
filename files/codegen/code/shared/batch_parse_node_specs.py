"""Batch parse TypeScript node spec files using the AST extractor."""

import json
import subprocess
import tempfile
import os
import shutil
import platform
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
    parser_script = project_root / 'dipeo' / 'infrastructure' / 'adapters' / 'parsers' / 'typescript' / 'ts_ast_extractor.ts'
    
    print(f"Executing batch TypeScript parsing for {len(sources)} node spec files...")
    
    try:
        # Platform-specific command resolution
        if platform.system() == 'Windows':
            # Try to find pnpm in PATH or common locations
            pnpm_cmd = None
            
            # First try pnpm.CMD in PATH
            if shutil.which('pnpm.CMD'):
                pnpm_cmd = 'pnpm.CMD'
            elif shutil.which('pnpm'):
                pnpm_cmd = 'pnpm'
            else:
                # Try common pnpm installation locations
                possible_pnpm_paths = [
                    os.path.expanduser('~\\AppData\\Local\\pnpm\\pnpm.CMD'),
                    os.path.expanduser('~\\AppData\\Roaming\\npm\\pnpm.CMD'),
                    'C:\\Program Files\\nodejs\\pnpm.CMD',
                    'C:\\Program Files (x86)\\nodejs\\pnpm.CMD',
                ]
                
                for path in possible_pnpm_paths:
                    if os.path.exists(path):
                        pnpm_cmd = path
                        break
            
            # Build command based on available tools
            if not pnpm_cmd and shutil.which('npx.CMD'):
                cmd = ['npx.CMD', 'tsx', str(parser_script)]
            elif not pnpm_cmd and shutil.which('npx'):
                cmd = ['npx', 'tsx', str(parser_script)]
            elif pnpm_cmd:
                cmd = [pnpm_cmd, 'tsx', str(parser_script)]
            else:
                # Last resort: try node directly with tsx
                node_cmd = shutil.which('node') or 'node'
                tsx_path = project_root / 'node_modules' / '.bin' / 'tsx'
                if not tsx_path.exists():
                    tsx_path = project_root / 'node_modules' / '.bin' / 'tsx.CMD'
                if tsx_path.exists():
                    cmd = [node_cmd, str(tsx_path), str(parser_script)]
                else:
                    raise RuntimeError('Could not find pnpm, npx, or tsx to run TypeScript parser')
            
            # Add GitHub Actions paths to subprocess environment
            env = os.environ.copy()
            if 'GITHUB_ACTIONS' in env:
                # In GitHub Actions, ensure we have access to installed tools
                github_path = env.get('GITHUB_PATH', '')
                if github_path and os.path.exists(github_path):
                    with open(github_path, 'r') as f:
                        additional_paths = f.read().strip().split('\n')
                        current_path = env.get('PATH', '')
                        env['PATH'] = os.pathsep.join(additional_paths + [current_path])
        else:
            # On Unix-like systems, use normal command
            cmd = ['pnpm', 'tsx', str(parser_script)]
            env = None
        
        # Add common arguments
        cmd.extend([
            f'--batch-input={tmp_file_path}',
            '--patterns=const',  # Node specs use export const
            '--include-jsdoc',
            '--mode=module'
        ])
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=str(project_root),
            env=env if platform.system() == 'Windows' else None,
            timeout=60
        )
        
        # Clean up temp file
        os.unlink(tmp_file_path)
        
        if result.returncode != 0:
            print(f"Parser failed with return code: {result.returncode}")
            print(f"Command was: {' '.join(cmd)}")
            print(f"Working directory: {project_root}")
            print(f"stderr: {result.stderr}")
            print(f"stdout: {result.stdout[:500]}...")
            # Check if this is a "command not found" error
            if "is not recognized" in result.stderr or "command not found" in result.stderr.lower():
                print(f"ERROR: TypeScript parser command not found. Check pnpm/npx installation.")
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