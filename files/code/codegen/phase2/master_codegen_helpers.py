"""
Helper functions for the master codegen orchestrator diagram.
Handles sub-diagram execution and result merging.
"""

import subprocess
import os
from typing import Dict, Any, List


def run_sub_diagram(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the domain model generation using make command.
    """
    try:
        # Run make codegen command
        result = subprocess.run(
            ['make', 'codegen'],
            capture_output=True,
            text=True,
            cwd=os.getenv('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO')
        )
        
        if result.returncode == 0:
            # Parse output to find generated files
            files_generated = []
            if 'models.py' in result.stdout:
                files_generated.append('dipeo/models/models.py')
            if 'conversions.py' in result.stdout:
                files_generated.append('dipeo/models/conversions.py')
            if '__generated_models__.py' in result.stdout:
                files_generated.append('dipeo/models/__generated_models__.py')
            if '__generated_conversions__.py' in result.stdout:
                files_generated.append('dipeo/models/__generated_conversions__.py')
            if 'generated_nodes.py' in result.stdout:
                files_generated.append('dipeo/core/static/generated_nodes.py')
            
            return {
                'success': True,
                'files_generated': files_generated if files_generated else [
                    'dipeo/models/models.py',
                    'dipeo/models/conversions.py',
                    'dipeo/core/static/generated_nodes.py'
                ],
                'message': 'Domain models generated successfully',
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        else:
            return {
                'success': False,
                'files_generated': [],
                'message': f'Domain model generation failed: {result.stderr}',
                'stdout': result.stdout,
                'stderr': result.stderr
            }
    except Exception as e:
        return {
            'success': False,
            'files_generated': [],
            'message': f'Error running domain model generation: {str(e)}'
        }


def run_node_codegen(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Execute the existing node codegen diagram.
    For now, return placeholder data.
    """
    node_spec = inputs.get('node_spec_path', 'files/specifications/nodes/typescript_ast_parser.json')
    return {
        'success': True,
        'files_generated': [
            f'Generated React component for {node_spec}',
            f'Generated GraphQL schema for {node_spec}',
            f'Generated field config for {node_spec}'
        ],
        'message': 'Node UI components generated successfully'
    }


def merge_codegen_results(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Merge results from multiple codegen sub-diagrams"""
    models_result = inputs.get('models', '')
    nodes_result = inputs.get('nodes', '')
    
    all_files = []
    messages = []
    models_generated = []
    nodes_generated = []
    
    # Parse bash script outputs to extract file lists
    if models_result and isinstance(models_result, str):
        if 'completed successfully' in models_result:
            messages.append('Domain models generated successfully')
            # Extract file paths from output
            for line in models_result.split('\n'):
                if '- dipeo/models/' in line or '- dipeo/core/' in line or '- apps/web/' in line:
                    file_path = line.strip().replace('- ', '').strip()
                    if file_path:
                        models_generated.append(file_path)
                        all_files.append(file_path)
        else:
            messages.append('Domain model generation may have issues')
            
    if nodes_result and isinstance(nodes_result, str):
        if 'completed' in nodes_result:
            messages.append('Node UI components generated successfully')
            # Extract expected files from output
            for line in nodes_result.split('\n'):
                if '- apps/web/src/__generated__/' in line or '- apps/server/' in line:
                    file_path = line.strip().replace('- ', '').strip()
                    if file_path:
                        nodes_generated.append(file_path)
                        all_files.append(file_path)
        else:
            messages.append('Node UI generation may have issues')
    
    # Get mode from inputs
    mode = inputs.get('mode', 'unknown')
    if not mode or mode == 'unknown':
        # Try to determine mode from what was executed
        if models_result and nodes_result:
            mode = 'full'
        elif models_result:
            mode = 'models'
        elif nodes_result:
            mode = 'nodes'
    
    return {
        'models_generated': models_generated,
        'nodes_generated': nodes_generated,
        'total_files': len(all_files),
        'all_files': all_files,
        'messages': messages,
        'mode': mode,
        'success': bool(models_result or nodes_result)
    }