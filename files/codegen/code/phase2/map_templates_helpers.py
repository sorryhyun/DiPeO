"""
Helper functions for the map_templates diagram.
Handles template manifest parsing, template processing, and batch rendering.
"""

import asyncio
import json
import yaml
from typing import Dict, Any, List


def parse_template_manifest(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Parse template manifest and filter by mode"""
    manifest_content = inputs.get('manifest_content', '')
    mode = inputs.get('mode', 'full')
    
    manifest = yaml.safe_load(manifest_content)
    templates = manifest.get('templates', [])
    modes = manifest.get('modes', {})
    
    # Filter templates based on mode
    if mode != 'all' and mode in modes:
        mode_config = modes[mode]
        template_ids = mode_config.get('templates', [])
        if template_ids != 'all':
            templates = [t for t in templates if t['id'] in template_ids]
    
    return {
        'templates': templates,
        'engines': manifest.get('engines', {}),
        'formatters': manifest.get('formatters', {}),
        'post_processors': manifest.get('post_processors', {}),
        'total_templates': len(templates)
    }


def process_template_batch(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Process all templates and prepare for rendering"""
    templates = inputs.get('templates', [])
    spec_data = inputs.get('spec_data', {})
    
    # Group templates by category for better organization
    categorized = {}
    render_queue = []
    
    for template in templates:
        category = template.get('category', 'other')
        if category not in categorized:
            categorized[category] = []
            
        # Prepare render context for each template
        render_context = {
            'template_id': template['id'],
            'template_config': template,
            'spec_data': spec_data,
            'context': {
                'spec_data': spec_data,
                'metadata': spec_data.get('_metadata', {})
            }
        }
        
        categorized[category].append(template)
        render_queue.append(render_context)
    
    return {
        'render_queue': render_queue,
        'categorized_templates': categorized,
        'queue_size': len(render_queue)
    }


def batch_render_templates(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate batch rendering of templates"""
    render_queue = inputs.get('render_queue', [])
    results = []
    errors = []
    
    for item in render_queue:
        template_config = item['template_config']
        spec_data = item['spec_data']
        
        # Simulate rendering result
        result = {
            'template_id': template_config['id'],
            'status': 'success',
            'output_path': template_config['output'].replace('{{spec_data.nodeType}}', spec_data.get('nodeType', 'unknown')),
            'category': template_config.get('category', 'other'),
            'content': f"// Generated content for {template_config['name']}"
        }
        
        # Check for optional templates
        if template_config.get('optional', False):
            result['skipped'] = True
            result['reason'] = 'Optional template'
            
        results.append(result)
    
    return {
        'render_results': results,
        'total_rendered': len([r for r in results if r['status'] == 'success' and not r.get('skipped')]),
        'total_skipped': len([r for r in results if r.get('skipped')]),
        'errors': errors
    }


def collect_render_results(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Collect and organize all rendering results"""
    render_results = inputs.get('render_results', [])
    
    # Group by category
    by_category = {}
    all_files = []
    
    for result in render_results:
        if result['status'] == 'success' and not result.get('skipped'):
            category = result['category']
            if category not in by_category:
                by_category[category] = []
            by_category[category].append(result['output_path'])
            all_files.append(result['output_path'])
    
    return {
        'files_by_category': by_category,
        'all_generated_files': all_files,
        'summary': {
            'total_files': len(all_files),
            'categories': list(by_category.keys()),
            'render_results': render_results
        }
    }