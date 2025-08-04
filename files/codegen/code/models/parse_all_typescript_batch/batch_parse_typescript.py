"""Batch parse TypeScript files using the AST extractor."""
import json
import subprocess
import tempfile
import os
import shutil
from pathlib import Path
from typing import Dict, Any


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main entry point for batch TypeScript parsing.
    
    Args:
        inputs: Dictionary containing 'sources' labeled input
        
    Returns:
        Dictionary containing:
        - parsed_results: Mapped parse results  
        - metadata: Batch processing metadata
    """
    # When receiving from labeled connections, inputs['label'] contains the labeled output
    sources_data = inputs.get('sources', {})
    # Handle case where we get the full node output vs just the sources
    if isinstance(sources_data, dict) and 'sources' in sources_data:
        sources = sources_data['sources']
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
    
    print(f"Executing batch TypeScript parsing for {len(sources)} files...")
    
    try:
        # On Windows, use pnpm.CMD to avoid bash PATH issues
        import platform
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
            
            # If pnpm not found, try npx as fallback
            if not pnpm_cmd and shutil.which('npx.CMD'):
                cmd = ['npx.CMD', 'tsx', str(parser_script), f'--batch-input={tmp_file_path}', '--patterns=interface,type,enum,const', '--include-jsdoc', '--mode=module']
            elif not pnpm_cmd and shutil.which('npx'):
                cmd = ['npx', 'tsx', str(parser_script), f'--batch-input={tmp_file_path}', '--patterns=interface,type,enum,const', '--include-jsdoc', '--mode=module']
            elif pnpm_cmd:
                cmd = [pnpm_cmd, 'tsx', str(parser_script), f'--batch-input={tmp_file_path}', '--patterns=interface,type,enum,const', '--include-jsdoc', '--mode=module']
            else:
                # Last resort: try node directly with tsx
                node_cmd = shutil.which('node') or 'node'
                tsx_path = project_root / 'node_modules' / '.bin' / 'tsx'
                if not tsx_path.exists():
                    tsx_path = project_root / 'node_modules' / '.bin' / 'tsx.CMD'
                if tsx_path.exists():
                    cmd = [node_cmd, str(tsx_path), str(parser_script), f'--batch-input={tmp_file_path}', '--patterns=interface,type,enum,const', '--include-jsdoc', '--mode=module']
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
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=str(project_root),
                env=env,
                timeout=60
            )
        else:
            # On Unix-like systems, use normal command
            cmd = [
                'pnpm', 'tsx', str(parser_script),
                f'--batch-input={tmp_file_path}',
                '--patterns=interface,type,enum,const',
                '--include-jsdoc',
                '--mode=module'
            ]
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
            print(f"Parser failed with return code: {result.returncode}")
            print(f"Command was: {' '.join(cmd)}")
            print(f"Working directory: {project_root}")
            print(f"stderr: {result.stderr}")
            print(f"stdout: {result.stdout[:500]}...")
            # Check if this is a "command not found" error
            if "is not recognized" in result.stderr or "command not found" in result.stderr.lower():
                print(f"ERROR: TypeScript parser command not found. Check pnpm/npx installation.")
            raise RuntimeError(f"Parser failed: {result.stderr}")
        
        # Debug output
        print(f"Parser stdout length: {len(result.stdout)} chars")
        print(f"First 500 chars: {result.stdout[:500]}")
        
        # Parse the batch result
        if not result.stdout.strip():
            raise RuntimeError("Parser returned empty output")
        
        batch_result = json.loads(result.stdout)
        
        # Map results to simplified keys
        mapped_results = {}
        for file_path, parse_result in batch_result.get('results', {}).items():
            key = file_mapping.get(file_path, file_path)
            mapped_results[key] = parse_result
        
        # Log performance metrics
        if 'metadata' in batch_result:
            meta = batch_result['metadata']
            print(f"\n=== Batch Parsing Complete ===")
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


# Keep backward compatibility
def batch_parse_typescript(sources_data: Dict[str, Any]) -> Dict[str, Any]:
    """Legacy function for backward compatibility."""
    return main({'sources': sources_data})