"""
Helper functions for Phase 3 master codegen orchestrator.
Uses file-based communication between sub-diagrams.
"""
import json
import os
from typing import Dict, Any, List
from datetime import datetime


def prepare_execution_context(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Prepare execution context for sub-diagrams"""
    mode = inputs.get('mode', 'full')
    node_spec_path = inputs.get('node_spec_path', '')
    
    # Create execution ID for this run
    execution_id = f"codegen_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    # Ensure output directory exists
    output_dir = f"logs/codegen/runs/{execution_id}"
    os.makedirs(output_dir, exist_ok=True)
    
    return {
        'mode': mode,
        'node_spec_path': node_spec_path,
        'execution_id': execution_id,
        'output_dir': output_dir,
        'should_run_models': mode in ['full', 'models'],
        'should_run_nodes': mode in ['full', 'nodes']
    }


def read_sub_diagram_results(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Read results from sub-diagram output files"""
    execution_id = inputs.get('execution_id', '')
    output_dir = inputs.get('output_dir', '')
    
    results = {
        'models_result': None,
        'nodes_result': None,
        'execution_id': execution_id
    }
    
    # Read domain models results if exists
    models_file = os.path.join(output_dir, 'domain_models_result.json')
    if os.path.exists(models_file):
        try:
            with open(models_file, 'r') as f:
                results['models_result'] = json.load(f)
        except Exception as e:
            results['models_result'] = {'error': str(e)}
    
    # Read node UI results if exists
    nodes_file = os.path.join(output_dir, 'node_ui_result.json')
    if os.path.exists(nodes_file):
        try:
            with open(nodes_file, 'r') as f:
                results['nodes_result'] = json.load(f)
        except Exception as e:
            results['nodes_result'] = {'error': str(e)}
    
    return results


def generate_final_report(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """Generate final report from collected results"""
    models_result = inputs.get('models_result', {})
    nodes_result = inputs.get('nodes_result', {})
    mode = inputs.get('mode', 'unknown')
    execution_id = inputs.get('execution_id', '')
    
    # Collect all generated files
    all_files = []
    models_files = []
    nodes_files = []
    messages = []
    
    # Process model results
    if models_result:
        if models_result.get('success'):
            models_files = models_result.get('files_generated', [])
            all_files.extend(models_files)
            messages.append(models_result.get('message', 'Domain models generated'))
        elif 'error' in models_result:
            messages.append(f"Domain model error: {models_result['error']}")
    
    # Process node results  
    if nodes_result:
        if nodes_result.get('success'):
            nodes_files = nodes_result.get('files_generated', [])
            all_files.extend(nodes_files)
            messages.append(nodes_result.get('message', 'Node UI generated'))
        elif 'error' in nodes_result:
            messages.append(f"Node UI error: {nodes_result['error']}")
    
    return {
        'execution_id': execution_id,
        'mode': mode,
        'total_files': len(all_files),
        'models_generated': models_files,
        'nodes_generated': nodes_files,
        'all_files': all_files,
        'messages': messages,
        'timestamp': datetime.now().isoformat()
    }


def save_final_report(inputs: Dict[str, Any]) -> str:
    """Save the final report and return summary text"""
    report_data = inputs
    execution_id = report_data.get('execution_id', '')
    output_dir = f"logs/codegen/runs/{execution_id}"
    
    # Save detailed JSON report
    report_file = os.path.join(output_dir, 'final_report.json')
    with open(report_file, 'w') as f:
        json.dump(report_data, f, indent=2)
    
    # Generate summary text
    summary_lines = [
        f"Code Generation Complete - {report_data.get('timestamp', '')}",
        f"Execution ID: {execution_id}",
        f"Mode: {report_data.get('mode', 'unknown')}",
        f"Total files generated: {report_data.get('total_files', 0)}",
        ""
    ]
    
    if report_data.get('models_generated'):
        summary_lines.append("Domain Model Files:")
        for f in report_data['models_generated']:
            summary_lines.append(f"  - {f}")
        summary_lines.append("")
    
    if report_data.get('nodes_generated'):
        summary_lines.append("Node UI Files:")
        for f in report_data['nodes_generated']:
            summary_lines.append(f"  - {f}")
        summary_lines.append("")
    
    if report_data.get('messages'):
        summary_lines.append("Messages:")
        for msg in report_data['messages']:
            summary_lines.append(f"  - {msg}")
    
    summary_lines.append(f"\nFull report saved to: {report_file}")
    
    return '\n'.join(summary_lines)