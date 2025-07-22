#!/usr/bin/env python3
"""
Run code generation for a specific node specification.
"""

import os
import sys
import yaml
import json
import subprocess
import tempfile
from pathlib import Path

def create_temp_diagram(spec_path):
    """Create a temporary diagram with the spec path filled in."""
    # Read the template diagram
    diagram_path = Path('files/diagrams/codegen/main.light.yaml')
    with open(diagram_path, 'r') as f:
        diagram = yaml.safe_load(f)
    
    # Update the start node's custom_data with the actual spec path
    for node in diagram['nodes']:
        if node['label'] == 'Start':
            node['props']['custom_data']['node_spec_path'] = spec_path
            break
    
    # Create a temporary file with the updated diagram
    with tempfile.NamedTemporaryFile(mode='w', suffix='.light.yaml', delete=False) as f:
        yaml.dump(diagram, f, default_flow_style=False, sort_keys=False)
        return f.name

def main():
    if len(sys.argv) != 2:
        print("Usage: python scripts/run_codegen.py <node_spec_path>")
        sys.exit(1)
    
    spec_path = sys.argv[1]
    
    # Verify spec file exists
    if not os.path.exists(spec_path):
        print(f"Error: Spec file not found: {spec_path}")
        sys.exit(1)
    
    print(f"🔄 Generating code for: {spec_path}")
    
    try:
        # Create temporary diagram with filled spec path
        temp_diagram = create_temp_diagram(spec_path)
        
        # Run the diagram
        cmd = [
            'dipeo', 'run', temp_diagram,
            '--no-browser',
            '--timeout=60'
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Clean up temp file
        os.unlink(temp_diagram)
        
        if result.returncode == 0:
            print("✅ Code generation completed successfully!")
            if result.stdout:
                print(result.stdout)
        else:
            print("❌ Code generation failed!")
            if result.stderr:
                print(f"Error: {result.stderr}")
            if result.stdout:
                print(result.stdout)
            sys.exit(1)
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()