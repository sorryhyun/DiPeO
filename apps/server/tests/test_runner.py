#!/usr/bin/env python3
"""Simple test runner to verify consolidated tests work."""

import subprocess
import sys
from pathlib import Path


def run_test_suite(test_path):
    """Run a specific test suite and return results."""
    cmd = [sys.executable, "-m", "pytest", test_path, "-v", "--tb=short"]
    result = subprocess.run(cmd, check=False, capture_output=True, text=True)
    return result.returncode, result.stdout, result.stderr


def main():
    """Run all test suites and report results."""
    server_dir = Path(__file__).parent.parent
    test_suites = [
        ("REST Freeze Tests", "tests/test_rest_freeze.py"),
        ("Health/Metrics Tests", "tests/test_health_metrics.py"),
        ("Upload Tests", "tests/test_graphql_upload.py"),
        ("Diagram Mutations", "tests/mutations/test_diagram_mutations.py"),
        ("Person Mutations", "tests/mutations/test_person_mutations.py"),
        ("Execution Mutations", "tests/mutations/test_execution_mutations.py"),
        ("Execution Flow Integration", "tests/integration/test_execution_flow.py"),
        ("Interactive Flow Integration", "tests/integration/test_interactive_flow.py"),
        ("Error Scenarios Integration", "tests/integration/test_error_scenarios.py"),
    ]

    print("DiPeO Server Test Suite Runner")
    print("=" * 50)

    total_passed = 0
    total_failed = 0

    for name, test_path in test_suites:
        print(f"\nRunning {name}...")
        full_path = server_dir / test_path

        if not full_path.exists():
            print(f"  ❌ Test file not found: {test_path}")
            continue

        returncode, stdout, stderr = run_test_suite(full_path)

        # Parse results
        if "passed" in stdout:
            passed_match = stdout.split("passed")[0].strip().split()[-1]
            try:
                passed = int(passed_match)
                total_passed += passed
                print(f"  ✅ {passed} tests passed")
            except:
                pass

        if "failed" in stdout:
            failed_match = stdout.split("failed")[0].strip().split()[-1]
            try:
                failed = int(failed_match)
                total_failed += failed
                print(f"  ❌ {failed} tests failed")
            except:
                pass

        if "error" in stdout.lower() and returncode != 0:
            print("  ⚠️  Errors during collection/execution")

    print("\n" + "=" * 50)
    print(f"Total Results: {total_passed} passed, {total_failed} failed")

    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
