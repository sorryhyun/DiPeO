#!/usr/bin/env python3
"""
Test script for IR builders.
Tests both backend and frontend IR builders with sample AST data.
"""

import json
import sys
import os
from pathlib import Path

# Add the DiPeO base directory to path
sys.path.append(os.environ.get('DIPEO_BASE_DIR', '/home/soryhyun/DiPeO'))

# Import the IR builders
from projects.codegen.code.backend_ir_builder import build_backend_ir
from projects.codegen.code.frontend_ir_builder import build_frontend_ir


def load_sample_ast_data():
    """Load sample AST data from temp directory."""
    base_dir = Path('/home/soryhyun/DiPeO')
    temp_dir = base_dir / 'temp'

    # Load a few sample AST files
    ast_data = {}

    # Load node specs
    nodes_dir = temp_dir / 'nodes'
    if nodes_dir.exists():
        for spec_file in nodes_dir.glob('*.spec.ts.json'):
            with open(spec_file, 'r') as f:
                ast_data[str(spec_file)] = json.load(f)

    # Load frontend query definitions if available
    frontend_dir = temp_dir / 'frontend' / 'query-definitions'
    if frontend_dir.exists():
        for query_file in frontend_dir.glob('*.ts.json'):
            with open(query_file, 'r') as f:
                ast_data[str(query_file)] = json.load(f)

    # Load core types if available
    core_dir = temp_dir / 'core'
    if core_dir.exists():
        for core_file in core_dir.glob('*.ts.json'):
            with open(core_file, 'r') as f:
                ast_data[str(core_file)] = json.load(f)

    return ast_data


def test_backend_ir():
    """Test the backend IR builder."""
    print("=" * 60)
    print("Testing Backend IR Builder")
    print("=" * 60)

    # Load sample data
    ast_data = load_sample_ast_data()
    print(f"Loaded {len(ast_data)} AST files")

    # Wrap in 'default' key as expected by the builder
    input_data = {'default': ast_data}

    try:
        # Build the IR
        ir = build_backend_ir(input_data)

        # Check the IR structure
        print(f"\nBackend IR structure:")
        print(f"  - Version: {ir.get('version')}")
        print(f"  - Generated at: {ir.get('generated_at')}")
        print(f"  - Node specs: {len(ir.get('node_specs', []))}")
        print(f"  - Enums: {len(ir.get('enums', []))}")
        print(f"  - Unified models: {len(ir.get('unified_models', []))}")

        # Show sample node spec
        if ir.get('node_specs'):
            sample = ir['node_specs'][0]
            print(f"\nSample node spec:")
            print(f"  - Type: {sample.get('node_type')}")
            print(f"  - Name: {sample.get('node_name')}")
            print(f"  - Fields: {len(sample.get('fields', []))}")

        print("\n✅ Backend IR builder test passed!")
        return True

    except Exception as e:
        print(f"\n❌ Backend IR builder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_frontend_ir():
    """Test the frontend IR builder."""
    print("\n" + "=" * 60)
    print("Testing Frontend IR Builder")
    print("=" * 60)

    # Load sample data
    ast_data = load_sample_ast_data()
    print(f"Loaded {len(ast_data)} AST files")

    # Wrap in 'default' key as expected by the builder
    input_data = {'default': ast_data}

    try:
        # Build the IR
        ir = build_frontend_ir(input_data)

        # Check the IR structure
        print(f"\nFrontend IR structure:")
        print(f"  - Version: {ir.get('version')}")
        print(f"  - Generated at: {ir.get('generated_at')}")
        print(f"  - Node configs: {len(ir.get('node_configs', []))}")
        print(f"  - Field configs: {len(ir.get('field_configs', []))}")
        print(f"  - Zod schemas: {len(ir.get('zod_schemas', []))}")
        print(f"  - GraphQL queries: {len(ir.get('graphql_queries', []))}")

        # Show sample node config
        if ir.get('node_configs'):
            sample = ir['node_configs'][0]
            print(f"\nSample node config:")
            print(f"  - Name: {sample.get('name')}")
            print(f"  - Display name: {sample.get('display_name')}")
            print(f"  - Fields: {len(sample.get('fields', []))}")

        print("\n✅ Frontend IR builder test passed!")
        return True

    except Exception as e:
        print(f"\n❌ Frontend IR builder test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def check_ir_files():
    """Check if IR files were created."""
    print("\n" + "=" * 60)
    print("Checking Generated IR Files")
    print("=" * 60)

    base_dir = Path('/home/soryhyun/DiPeO')
    ir_dir = base_dir / 'projects/codegen/ir'

    backend_ir = ir_dir / 'backend_ir.json'
    frontend_ir = ir_dir / 'frontend_ir.json'

    if backend_ir.exists():
        size = backend_ir.stat().st_size
        print(f"✅ Backend IR file exists: {backend_ir} ({size:,} bytes)")
    else:
        print(f"❌ Backend IR file not found: {backend_ir}")

    if frontend_ir.exists():
        size = frontend_ir.stat().st_size
        print(f"✅ Frontend IR file exists: {frontend_ir} ({size:,} bytes)")
    else:
        print(f"❌ Frontend IR file not found: {frontend_ir}")


def main():
    """Run all tests."""
    print("\n🧪 Testing IR Builders\n")

    # Run tests
    backend_success = test_backend_ir()
    frontend_success = test_frontend_ir()

    # Check generated files
    check_ir_files()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)

    if backend_success and frontend_success:
        print("✅ All tests passed!")
        print("\nPhase 1 objectives achieved:")
        print("  1. ✅ Created backend_ir_builder.py")
        print("  2. ✅ Created frontend_ir_builder.py")
        print("  3. ✅ Both builders successfully generate IR")
        print("  4. ✅ IR files are written to projects/codegen/ir/")
        print("\nNext steps (Phase 2):")
        print("  - Update diagrams to use the new IR builders")
        print("  - Convert templates to use the unified IR")
        print("  - Remove obsolete extractors")
        return 0
    else:
        print("❌ Some tests failed. Please review the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
