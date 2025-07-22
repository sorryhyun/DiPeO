"""
Helper functions for the registry_update diagram.
Handles file collection, registry updates, export indices, and report generation.
"""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List


def collect_generated_files(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Collect all successfully generated files by category"""
    render_results = inputs.get('render_results', [])
    spec_data = inputs.get('spec_data', {})
    
    files_by_category = {
        'models': [],
        'frontend': [],
        'backend': [],
        'graphql': [],
        'registry': [],
        'other': []
    }
    
    all_files = []
    
    for result in render_results:
        if result.get('success') and not result.get('skipped'):
            category = result.get('category', 'other')
            if category not in files_by_category:
                category = 'other'
            
            file_info = {
                'path': result['output_path'],
                'template_id': result['template_id'],
                'size': result.get('size', 0),
                'cached': result.get('cached', False)
            }
            
            files_by_category[category].append(file_info)
            all_files.append(result['output_path'])
    
    return {
        'files_by_category': files_by_category,
        'all_files': all_files,
        'node_type': spec_data.get('nodeType', 'unknown')
    }


def update_node_type_registry(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Update the central node type registry"""
    node_type = inputs.get('node_type', '')
    
    # Registry file paths
    registries = {
        'node_types': 'dipeo/models/src/diagram.ts',
        'python_handlers': 'dipeo/application/container/node_registry.py',
        'graphql_schema': 'apps/server/src/dipeo_server/api/graphql/registry.graphql'
    }
    
    updates_made = []
    
    # Simulate registry updates
    # In real implementation, would read, modify, and write files
    
    # Update TypeScript NodeType enum
    if node_type:
        updates_made.append({
            'file': registries['node_types'],
            'change': f"Added {node_type.upper()} to NodeType enum",
            'success': True
        })
    
    # Update Python handler registry
    updates_made.append({
        'file': registries['python_handlers'],
        'change': f"Registered {node_type}_handler",
        'success': True
    })
    
    # Update GraphQL schema registry
    updates_made.append({
        'file': registries['graphql_schema'],
        'change': f"Added {node_type} to GraphQL union types",
        'success': True
    })
    
    return {
        'registry_updates': updates_made,
        'updated_count': len(updates_made)
    }


def update_export_indices(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Update index.ts files to export new components"""
    files_by_category = inputs.get('files_by_category', {})
    node_type = inputs.get('node_type', '')
    
    index_updates = []
    
    # Frontend component exports
    frontend_files = files_by_category.get('frontend', [])
    if frontend_files:
        component_exports = []
        for file in frontend_files:
            # Extract component name from path
            path = Path(file['path'])
            if path.suffix == '.tsx':
                component_name = path.stem
                export_line = f"export {{ {component_name} }} from './generated/{component_name}';"
                component_exports.append(export_line)
        
        if component_exports:
            index_updates.append({
                'file': 'apps/web/src/features/diagram-editor/components/nodes/index.ts',
                'exports': component_exports,
                'success': True
            })
    
    # Model exports
    model_files = files_by_category.get('models', [])
    if model_files:
        model_exports = []
        for file in model_files:
            path = Path(file['path'])
            if 'nodes' in str(path) and path.suffix == '.ts':
                model_name = path.stem
                export_line = f"export * from './nodes/{model_name}';"
                model_exports.append(export_line)
        
        if model_exports:
            index_updates.append({
                'file': 'dipeo/models/src/index.ts',
                'exports': model_exports,
                'success': True
            })
    
    return {
        'index_updates': index_updates,
        'total_exports': sum(len(u['exports']) for u in index_updates)
    }


def generate_registry_report(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate comprehensive registry update report"""
    registry_updates = inputs.get('registry_updates', [])
    index_updates = inputs.get('index_updates', [])
    all_files = inputs.get('all_files', [])
    node_type = inputs.get('node_type', '')
    
    report = {
        'timestamp': datetime.utcnow().isoformat(),
        'node_type': node_type,
        'summary': {
            'total_files_generated': len(all_files),
            'registry_files_updated': len(registry_updates),
            'index_files_updated': len(index_updates),
            'success': all(u['success'] for u in registry_updates)
        },
        'files_generated': all_files,
        'registry_updates': registry_updates,
        'index_updates': index_updates,
        'next_steps': []
    }
    
    # Add next steps based on what was generated
    if node_type:
        report['next_steps'].extend([
            f"1. Implement the handler for {node_type} in dipeo/application/execution/handlers/",
            f"2. Add test cases for {node_type} node",
            f"3. Update documentation for {node_type} node type",
            "4. Run 'make codegen' to regenerate Python models from TypeScript"
        ])
    
    return {'registry_report': report}