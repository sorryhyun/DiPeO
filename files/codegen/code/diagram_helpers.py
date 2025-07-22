"""
Helper functions for diagram-based code generation system.
Provides utility functions for file operations, template processing, and caching.
"""

import os
import hashlib
import tempfile
import subprocess
import glob
import json
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime

# Get project root from environment or use current working directory
PROJECT_ROOT = Path(os.getenv('DIPEO_BASE_DIR', os.getcwd()))


def main(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Main entry point - provides information about available functions."""
    return {
        "message": "DiPeO Diagram Helper Functions",
        "available_functions": [
            "file_glob",
            "write_file_atomic", 
            "format_code",
            "hash_content",
            "check_file_cache",
            "run_sub_diagram",
            "sort_graphql_definitions",
            "add_generated_header",
            "validate_and_fix_imports"
        ],
        "description": "Helper functions for diagram-based code generation"
    }


def file_glob(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Find files matching glob patterns.
    
    Inputs:
        pattern: Glob pattern (e.g., "**/*.ts")
        path: Base path to search from (default: project root)
        exclude: List of patterns to exclude
    """
    pattern = inputs.get('pattern', '**/*')
    base_path = inputs.get('path', str(PROJECT_ROOT))
    exclude_patterns = inputs.get('exclude', [])
    
    # Find all matching files
    full_pattern = os.path.join(base_path, pattern)
    files = glob.glob(full_pattern, recursive=True)
    
    # Apply exclusions
    if exclude_patterns:
        filtered_files = []
        for file in files:
            excluded = False
            for exclude in exclude_patterns:
                if glob.fnmatch.fnmatch(file, exclude):
                    excluded = True
                    break
            if not excluded:
                filtered_files.append(file)
        files = filtered_files
    
    # Get file info
    file_info = []
    for file_path in files:
        try:
            stat = os.stat(file_path)
            file_info.append({
                'path': file_path,
                'name': os.path.basename(file_path),
                'size': stat.st_size,
                'modified': datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
        except:
            pass
    
    return {
        'files': file_info,
        'count': len(file_info),
        'pattern': pattern,
        'base_path': base_path
    }


def write_file_atomic(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Write file atomically using temp file + rename.
    
    Inputs:
        path: Output file path
        content: File content to write
        backup: Whether to backup existing file (default: False)
        mode: File mode (default: 'w')
    """
    file_path = inputs.get('path', inputs.get('output_path', ''))
    content = inputs.get('content', '')
    backup = inputs.get('backup', False)
    mode = inputs.get('mode', 'w')
    
    if not file_path:
        return {'error': 'No file path provided'}
    
    file_path = Path(file_path)
    
    # Ensure directory exists
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Backup existing file if requested
    if backup and file_path.exists():
        backup_path = file_path.with_suffix(file_path.suffix + '.backup')
        file_path.rename(backup_path)
    
    # Write to temporary file first
    try:
        with tempfile.NamedTemporaryFile(
            mode=mode,
            delete=False,
            dir=file_path.parent,
            prefix=f'.{file_path.name}.',
            suffix='.tmp'
        ) as tmp:
            tmp.write(content)
            tmp_path = tmp.name
        
        # Atomic rename
        os.rename(tmp_path, str(file_path))
        
        return {
            'success': True,
            'path': str(file_path),
            'size': len(content),
            'backed_up': backup and file_path.exists()
        }
    except Exception as e:
        # Clean up temp file if it exists
        if 'tmp_path' in locals() and os.path.exists(tmp_path):
            os.unlink(tmp_path)
        return {
            'success': False,
            'error': str(e)
        }


def format_code(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Format code using appropriate formatter based on file extension.
    
    Inputs:
        path: File path to format
        formatter: Override formatter (optional)
        check_only: Only check if formatting is needed (default: False)
    """
    file_path = inputs.get('path', '')
    formatter_override = inputs.get('formatter', None)
    check_only = inputs.get('check_only', False)
    
    if not file_path or not os.path.exists(file_path):
        return {'error': 'File not found'}
    
    # Determine formatter based on file extension
    ext = os.path.splitext(file_path)[1]
    
    formatter_map = {
        '.py': ['black', file_path],
        '.ts': ['pnpm', 'prettier', '--write', file_path],
        '.tsx': ['pnpm', 'prettier', '--write', file_path],
        '.js': ['pnpm', 'prettier', '--write', file_path],
        '.jsx': ['pnpm', 'prettier', '--write', file_path],
        '.json': ['pnpm', 'prettier', '--write', file_path],
        '.yaml': ['pnpm', 'prettier', '--write', file_path],
        '.yml': ['pnpm', 'prettier', '--write', file_path],
        '.graphql': ['pnpm', 'prettier', '--write', file_path],
        '.gql': ['pnpm', 'prettier', '--write', file_path]
    }
    
    if formatter_override:
        # Use override formatter
        if formatter_override == 'prettier':
            cmd = ['pnpm', 'prettier', '--write', file_path]
        elif formatter_override == 'black':
            cmd = ['black', file_path]
        elif formatter_override == 'ruff':
            cmd = ['ruff', 'format', file_path]
        else:
            return {'error': f'Unknown formatter: {formatter_override}'}
    else:
        cmd = formatter_map.get(ext)
        if not cmd:
            return {
                'skipped': True,
                'reason': f'No formatter configured for {ext} files'
            }
    
    if check_only:
        # Modify command to check only
        if 'prettier' in cmd:
            cmd = cmd[:-1] + ['--check', file_path]
        elif 'black' in cmd:
            cmd = cmd + ['--check']
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            'success': result.returncode == 0,
            'formatted': not check_only and result.returncode == 0,
            'command': ' '.join(cmd),
            'stdout': result.stdout,
            'stderr': result.stderr
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def hash_content(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute SHA-256 hash of content.
    
    Inputs:
        content: Content to hash
        file_path: Alternative - path to file to hash
    """
    content = inputs.get('content', None)
    file_path = inputs.get('file_path', None)
    
    if content is None and file_path:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            return {'error': f'Failed to read file: {e}'}
    
    if content is None:
        return {'error': 'No content or file_path provided'}
    
    # Ensure content is bytes
    if isinstance(content, str):
        content = content.encode('utf-8')
    
    content_hash = hashlib.sha256(content).hexdigest()
    
    return {
        'hash': content_hash,
        'algorithm': 'sha256',
        'size': len(content)
    }


def check_file_cache(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Check if file content has changed by comparing hashes.
    
    Inputs:
        file_path: Path to existing file
        new_content: New content to compare
        new_hash: Pre-computed hash of new content (optional)
    """
    file_path = inputs.get('file_path', '')
    new_content = inputs.get('new_content', '')
    new_hash = inputs.get('new_hash', None)
    
    if not os.path.exists(file_path):
        return {
            'exists': False,
            'changed': True,
            'reason': 'File does not exist'
        }
    
    # Compute new content hash if not provided
    if new_hash is None:
        new_hash = hashlib.sha256(new_content.encode('utf-8')).hexdigest()
    
    # Read and hash existing file
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
            existing_hash = hashlib.sha256(existing_content.encode('utf-8')).hexdigest()
    except Exception as e:
        return {
            'exists': True,
            'changed': True,
            'reason': f'Error reading file: {e}'
        }
    
    changed = existing_hash != new_hash
    
    return {
        'exists': True,
        'changed': changed,
        'reason': 'Content unchanged' if not changed else 'Content differs',
        'existing_hash': existing_hash,
        'new_hash': new_hash
    }


def run_sub_diagram(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Simulate running a sub-diagram (placeholder for actual implementation).
    
    Inputs:
        diagram_path: Path to sub-diagram
        context: Context data to pass to sub-diagram
    """
    diagram_path = inputs.get('diagram_path', '')
    context = inputs.get('context', {})
    
    # This is a placeholder - in real implementation would execute the diagram
    print(f"Would execute sub-diagram: {diagram_path}")
    print(f"With context: {json.dumps(context, indent=2)}")
    
    # Return simulated result
    return {
        'success': True,
        'diagram': diagram_path,
        'message': f'Sub-diagram {diagram_path} executed successfully',
        'outputs': context  # Pass through for now
    }


def sort_graphql_definitions(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sort GraphQL type definitions alphabetically.
    
    Inputs:
        content: GraphQL schema content
    """
    content = inputs.get('content', '')
    
    # Simple line-based sorting for now
    # In real implementation would parse and sort properly
    lines = content.split('\n')
    
    # Group lines into definitions
    definitions = []
    current_def = []
    
    for line in lines:
        if line.strip() and not line.startswith(' ') and not line.startswith('\t'):
            if current_def:
                definitions.append('\n'.join(current_def))
            current_def = [line]
        else:
            current_def.append(line)
    
    if current_def:
        definitions.append('\n'.join(current_def))
    
    # Sort definitions
    definitions.sort()
    
    sorted_content = '\n\n'.join(definitions)
    
    return {
        'content': sorted_content,
        'definition_count': len(definitions)
    }


def add_generated_header(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add a generated file header comment.
    
    Inputs:
        content: File content
        file_type: Type of file (for comment style)
        generator_name: Name of the generator
    """
    content = inputs.get('content', '')
    file_type = inputs.get('file_type', 'unknown')
    generator_name = inputs.get('generator_name', 'DiPeO Codegen')
    
    timestamp = datetime.utcnow().isoformat()
    
    # Determine comment style
    comment_styles = {
        'python': '#',
        'typescript': '//',
        'javascript': '//',
        'graphql': '#',
        'yaml': '#'
    }
    
    comment_char = comment_styles.get(file_type, '#')
    
    header = f"""{comment_char} AUTO-GENERATED FILE - DO NOT EDIT
{comment_char} Generated by: {generator_name}
{comment_char} Generated at: {timestamp}
{comment_char} Source: DiPeO Code Generation System

"""
    
    return {
        'content': header + content
    }


def validate_and_fix_imports(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and fix import statements in generated code.
    
    Inputs:
        content: File content
        file_type: Type of file
        project_root: Project root for relative imports
    """
    content = inputs.get('content', '')
    file_type = inputs.get('file_type', '')
    
    # This is a placeholder - real implementation would parse and fix imports
    # For now, just return the content unchanged
    
    issues_found = []
    fixes_applied = []
    
    # Simulate some validation
    if file_type == 'typescript' and 'import' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith('import') and '../../../' in line:
                issues_found.append(f"Line {i+1}: Deep relative import detected")
    
    return {
        'content': content,
        'issues_found': issues_found,
        'fixes_applied': fixes_applied,
        'valid': len(issues_found) == 0
    }