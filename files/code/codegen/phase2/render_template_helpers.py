"""
Helper functions for the render_template_sub diagram.
Handles template rendering, post-processing, caching, and file operations.
"""

import hashlib
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Any


def apply_post_processors(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Apply any configured post-processors to the content"""
    content = inputs.get('rendered_content', '')
    template_config = inputs.get('template_config', {})
    
    # Check for post-processor configuration
    post_processor = template_config.get('post_processor')
    if post_processor:
        # Simulate post-processing
        if post_processor == 'sort_graphql_defs':
            # Sort GraphQL definitions alphabetically
            lines = content.split('\n')
            # Simple simulation - in real implementation would parse and sort
            content = '\n'.join(sorted(lines))
        elif post_processor == 'add_header_comment':
            header = "// AUTO-GENERATED FILE - DO NOT EDIT\n\n"
            content = header + content
    
    return {'processed_content': content}


def compute_content_hash(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Compute SHA-256 hash of content for caching"""
    content = inputs.get('processed_content', '')
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    
    return {
        'content_hash': content_hash,
        'content_size': len(content)
    }


def check_write_cache(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Check if file exists and has same content hash"""
    output_path = inputs.get('output_path', '')
    new_hash = inputs.get('content_hash', '')
    
    # Check if file exists
    if os.path.exists(output_path):
        with open(output_path, 'r') as f:
            existing_content = f.read()
            existing_hash = hashlib.sha256(existing_content.encode()).hexdigest()
            
        if existing_hash == new_hash:
            return {
                'should_write': False,
                'reason': 'Content unchanged',
                'cached': True
            }
    
    return {
        'should_write': True,
        'reason': 'New or changed content',
        'cached': False
    }


def write_file_atomic(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Write file atomically using temp file + rename"""
    output_path = inputs.get('output_path', '')
    content = inputs.get('processed_content', '')
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    # Write to temporary file first
    with tempfile.NamedTemporaryFile(mode='w', delete=False, 
                                   dir=os.path.dirname(output_path)) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    # Atomic rename
    os.rename(tmp_path, output_path)
    
    return {
        'written': True,
        'path': output_path,
        'size': len(content)
    }


def format_generated_code(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Run formatter on generated file"""
    file_path = inputs.get('path', '')
    template_config = inputs.get('template_config', {})
    formatter = template_config.get('formatter')
    
    if not formatter:
        return {'formatted': False, 'reason': 'No formatter configured'}
    
    # Map formatter to command
    formatter_commands = {
        'prettier': ['pnpm', 'prettier', '--write', file_path],
        'black': ['black', file_path],
        'ruff': ['ruff', 'format', file_path]
    }
    
    if formatter in formatter_commands:
        try:
            # Simulate formatting - in real implementation would run command
            # subprocess.run(formatter_commands[formatter], check=True)
            return {'formatted': True, 'formatter': formatter}
        except Exception as e:
            return {'formatted': False, 'error': str(e)}
    
    return {'formatted': False, 'reason': f'Unknown formatter: {formatter}'}


def log_cache_hit(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Log that file was skipped due to cache hit"""
    return {
        'action': 'skipped',
        'reason': inputs.get('reason', 'Cache hit'),
        'output_path': inputs.get('output_path', '')
    }


def collect_render_result(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Collect all results from the rendering pipeline"""
    template_config = inputs.get('template_config', {})
    
    result = {
        'template_id': template_config.get('id', 'unknown'),
        'template_name': template_config.get('name', 'Unknown Template'),
        'output_path': inputs.get('output_path', ''),
        'success': True,
        'cached': inputs.get('cached', False),
        'formatted': inputs.get('formatted', False),
        'content_hash': inputs.get('content_hash', ''),
        'size': inputs.get('size', 0)
    }
    
    if inputs.get('action') == 'skipped':
        result['skipped'] = True
        result['skip_reason'] = inputs.get('reason', '')
        
    return {'render_result': result}