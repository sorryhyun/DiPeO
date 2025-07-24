#!/usr/bin/env python3
"""Test the codegen functions to verify data flow."""

import json
import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Import codegen functions directly
sys.path.insert(0, str(Path(__file__).parent))
from codegen import initialize_codegen, load_all_node_specs, get_next_spec, generate_all, update_progress

# Simulate the data flow through the diagram
print("=== Testing Diagram Data Flow ===\n")

# 1. Start node output (wrapped in 'default')
start_output = {
    'default': {
        'node_specs_dir': 'files/codegen/specifications/nodes'
    }
}
print(f"1. Start node output: {start_output}")

# 2. Initialize
init_result = initialize_codegen(start_output)
print(f"\n2. Initialize result: {list(init_result.keys())}")
print(f"   - node_specs_dir: {init_result.get('node_specs_dir')}")

# 3. Load all specs
specs_result = load_all_node_specs(init_result)
print(f"\n3. Load all specs result:")
print(f"   - total_nodes: {specs_result.get('total_nodes')}")
print(f"   - specs count: {len(specs_result.get('specs', []))}")

# 4. Get first spec
first_spec_result = get_next_spec(specs_result)
print(f"\n4. Get first spec result:")
print(f"   - current_spec: {first_spec_result.get('current_spec', {}).get('nodeType')}")

# 5. Generate files for first spec (if exists)
if first_spec_result.get('current_spec'):
    gen_result = generate_all(first_spec_result)
    print(f"\n5. Generate result:")
    print(f"   - success: {gen_result.get('success')}")
    print(f"   - files_generated: {len(gen_result.get('files_generated', []))}")
    
    # 6. Update progress
    progress_result = update_progress(gen_result)
    print(f"\n6. Update progress result:")
    print(f"   - current_index: {progress_result.get('current_index')}")
    print(f"   - results count: {len(progress_result.get('results', []))}")

print("\n=== Test Complete ===")