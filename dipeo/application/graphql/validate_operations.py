#!/usr/bin/env python
"""
Script to validate that all generated GraphQL operations have implementations.

This script checks:
1. All generated operations are mapped to resolvers
2. Operation query strings are available
3. Type safety is maintained
"""

import asyncio
import sys
from pathlib import Path

from dipeo.application.graphql.operation_executor import OperationExecutor
from dipeo.application.registry.enhanced_service_registry import (
    EnhancedServiceRegistry as ServiceRegistry,
)
from dipeo.diagram_generated.graphql import operations

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))


def get_all_generated_operations() -> set[str]:
    """Get all operation names from the generated module."""
    all_ops = set()

    for name in dir(operations):
        if name.endswith("Operation") and not name.startswith("_"):
            # Remove 'Operation' suffix to get the operation name
            op_name = name[: -len("Operation")]
            all_ops.add(op_name)

    return all_ops


def analyze_operation_coverage(executor: OperationExecutor) -> dict[str, any]:
    """Analyze which operations are implemented vs missing."""

    generated_ops = get_all_generated_operations()
    registered_ops = set(executor.operations.keys())

    # Find missing operations
    missing = generated_ops - registered_ops

    # Find extra operations (registered but not generated)
    extra = registered_ops - generated_ops

    # Calculate coverage
    coverage = (
        len(registered_ops & generated_ops) / len(generated_ops) * 100 if generated_ops else 0
    )

    return {
        "total_generated": len(generated_ops),
        "total_registered": len(registered_ops),
        "implemented": len(registered_ops & generated_ops),
        "missing": sorted(list(missing)),
        "extra": sorted(list(extra)),
        "coverage_percent": coverage,
    }


def categorize_operations(executor: OperationExecutor) -> dict[str, list[str]]:
    """Categorize operations by type (query, mutation, subscription)."""

    categories = {"queries": [], "mutations": [], "subscriptions": []}

    for op_name, mapping in executor.operations.items():
        op_type = mapping.operation_class.operation_type

        if op_type == "query":
            categories["queries"].append(op_name)
        elif op_type == "mutation":
            categories["mutations"].append(op_name)
        elif op_type == "subscription":
            categories["subscriptions"].append(op_name)

    # Sort each category
    for cat in categories:
        categories[cat].sort()

    return categories


def print_report(executor: OperationExecutor):
    """Print a detailed validation report."""

    print("=" * 80)
    print("GraphQL Operation Validation Report")
    print("=" * 80)
    print()

    # Coverage analysis
    coverage = analyze_operation_coverage(executor)

    print("📊 Coverage Summary:")
    print(f"  Total Generated Operations: {coverage['total_generated']}")
    print(f"  Total Registered Operations: {coverage['total_registered']}")
    print(f"  Implemented Operations: {coverage['implemented']}")
    print(f"  Coverage: {coverage['coverage_percent']:.1f}%")
    print()

    # Operation categories
    categories = categorize_operations(executor)

    print("📋 Operation Breakdown:")
    print(f"  Queries: {len(categories['queries'])}")
    print(f"  Mutations: {len(categories['mutations'])}")
    print(f"  Subscriptions: {len(categories['subscriptions'])}")
    print()

    # Missing operations
    if coverage["missing"]:
        print(f"❌ Missing Operations ({len(coverage['missing'])}):")
        for op in coverage["missing"]:
            print(f"    - {op}")
        print()
    else:
        print("✅ All generated operations are implemented!")
        print()

    # Extra operations
    if coverage["extra"]:
        print("⚠️  Extra Operations (registered but not generated):")
        for op in coverage["extra"]:
            print(f"    - {op}")
        print()

    # Detailed breakdown
    print("📝 Detailed Operation List:")
    print()

    print("  Queries:")
    for query in categories["queries"]:
        status = "✓" if query not in coverage["missing"] else "✗"
        print(f"    {status} {query}")
    print()

    print("  Mutations:")
    for mutation in categories["mutations"]:
        status = "✓" if mutation not in coverage["missing"] else "✗"
        print(f"    {status} {mutation}")
    print()

    if categories["subscriptions"]:
        print("  Subscriptions:")
        for sub in categories["subscriptions"]:
            status = "✓" if sub not in coverage["missing"] else "✗"
            print(f"    {status} {sub}")
        print()

    # Final status
    print("=" * 80)
    if not coverage["missing"]:
        print("✅ VALIDATION PASSED: All operations are implemented!")
    else:
        print(f"❌ VALIDATION FAILED: {len(coverage['missing'])} operations need implementation")
    print("=" * 80)

    # Return exit code
    return 0 if not coverage["missing"] else 1


async def main():
    """Main validation function."""

    try:
        # Create a minimal registry for testing
        registry = ServiceRegistry()

        # Initialize the operation executor
        executor = OperationExecutor(registry)

        # Print the validation report
        exit_code = print_report(executor)

        # Also validate that operations can be retrieved
        print("\n🔍 Testing Operation Query Retrieval:")
        test_ops = ["GetDiagram", "CreateNode", "ExecuteDiagram"]
        for op_name in test_ops:
            try:
                query = executor.get_operation_query(op_name)
                print(f"  ✓ {op_name}: Query string available ({len(query)} chars)")
            except ValueError as e:
                print(f"  ✗ {op_name}: {e}")

        print()

        # List all operations
        all_ops = executor.list_operations()
        print(f"📊 Total Operations Registered: {len(all_ops)}")

        return exit_code

    except Exception as e:
        print(f"❌ Error during validation: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
