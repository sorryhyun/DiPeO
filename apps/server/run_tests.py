#!/usr/bin/env python3
"""Test runner for DiPeO server tests."""

import sys
import subprocess
import argparse
from pathlib import Path
from typing import List, Optional


def run_command(cmd: List[str], cwd: Optional[Path] = None) -> int:
    """Run a command and return the exit code."""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd)
    return result.returncode


def run_unit_tests() -> int:
    """Run unit tests."""
    print("=" * 60)
    print("RUNNING UNIT TESTS")
    print("=" * 60)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_executors.py",
        "-v",
        "--tb=short",
        "-m", "not slow"
    ]
    
    return run_command(cmd, Path(__file__).parent)


def run_integration_tests() -> int:
    """Run integration tests."""
    print("=" * 60)
    print("RUNNING INTEGRATION TESTS")
    print("=" * 60)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_unified_execution_engine.py",
        "tests/test_api_integration.py",
        "-v",
        "--tb=short"
    ]
    
    return run_command(cmd, Path(__file__).parent)


def run_performance_tests() -> int:
    """Run performance tests."""
    print("=" * 60)
    print("RUNNING PERFORMANCE TESTS")
    print("=" * 60)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_performance.py",
        "-v",
        "--tb=short",
        "-m", "performance"
    ]
    
    return run_command(cmd, Path(__file__).parent)


def run_end_to_end_tests() -> int:
    """Run end-to-end tests."""
    print("=" * 60)
    print("RUNNING END-TO-END TESTS")
    print("=" * 60)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_end_to_end.py",
        "-v",
        "--tb=short",
        "-s"  # Show output for better debugging
    ]
    
    return run_command(cmd, Path(__file__).parent)


def run_all_tests() -> int:
    """Run all tests."""
    print("=" * 60)
    print("RUNNING ALL TESTS")
    print("=" * 60)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "-v",
        "--tb=short",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov"
    ]
    
    return run_command(cmd, Path(__file__).parent)


def run_coverage_report() -> int:
    """Generate coverage report."""
    print("=" * 60)
    print("GENERATING COVERAGE REPORT")
    print("=" * 60)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/",
        "--cov=src",
        "--cov-report=term-missing",
        "--cov-report=html:htmlcov",
        "--cov-report=xml:coverage.xml"
    ]
    
    return run_command(cmd, Path(__file__).parent)


def run_linting() -> int:
    """Run code linting."""
    print("=" * 60)
    print("RUNNING CODE LINTING")
    print("=" * 60)
    
    # Try to run flake8 if available
    try:
        cmd = ["flake8", "src/", "tests/"]
        return run_command(cmd, Path(__file__).parent)
    except FileNotFoundError:
        print("flake8 not installed, skipping linting")
        return 0


def run_type_checking() -> int:
    """Run type checking with mypy."""
    print("=" * 60)
    print("RUNNING TYPE CHECKING")
    print("=" * 60)
    
    # Try to run mypy if available
    try:
        cmd = ["mypy", "src/", "--ignore-missing-imports"]
        return run_command(cmd, Path(__file__).parent)
    except FileNotFoundError:
        print("mypy not installed, skipping type checking")
        return 0


def benchmark_execution() -> int:
    """Run execution benchmarks."""
    print("=" * 60)
    print("RUNNING EXECUTION BENCHMARKS")
    print("=" * 60)
    
    cmd = [
        sys.executable, "-m", "pytest",
        "tests/test_performance.py::TestExecutionPerformance",
        "-v",
        "--tb=short",
        "-s"
    ]
    
    return run_command(cmd, Path(__file__).parent)


def validate_installation() -> int:
    """Validate the installation."""
    print("=" * 60)
    print("VALIDATING INSTALLATION")
    print("=" * 60)
    
    # Check if required packages are available
    required_packages = [
        "fastapi",
        "uvicorn",
        "aiohttp", 
        "pytest",
        "pytest-asyncio",
        "pytest-cov"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\nMissing packages: {', '.join(missing_packages)}")
        print("Install with: pip install " + " ".join(missing_packages))
        return 1
    
    print("\n✓ All required packages are installed")
    return 0


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="DiPeO Server Test Runner")
    parser.add_argument(
        "test_type",
        choices=[
            "unit", "integration", "performance", "e2e", "all", 
            "coverage", "lint", "type", "benchmark", "validate"
        ],
        help="Type of tests to run"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )
    
    args = parser.parse_args()
    
    # Change to the server directory
    server_dir = Path(__file__).parent
    print(f"Running tests from: {server_dir}")
    
    exit_code = 0
    
    if args.test_type == "unit":
        exit_code = run_unit_tests()
    elif args.test_type == "integration":
        exit_code = run_integration_tests()
    elif args.test_type == "performance":
        exit_code = run_performance_tests()
    elif args.test_type == "e2e":
        exit_code = run_end_to_end_tests()
    elif args.test_type == "all":
        # Run all test types
        test_functions = [
            run_unit_tests,
            run_integration_tests,
            run_end_to_end_tests
        ]
        
        if not args.fast:
            test_functions.append(run_performance_tests)
        
        for test_func in test_functions:
            result = test_func()
            if result != 0:
                exit_code = result
                break  # Stop on first failure
    elif args.test_type == "coverage":
        exit_code = run_coverage_report()
    elif args.test_type == "lint":
        exit_code = run_linting()
    elif args.test_type == "type":
        exit_code = run_type_checking()
    elif args.test_type == "benchmark":
        exit_code = benchmark_execution()
    elif args.test_type == "validate":
        exit_code = validate_installation()
    
    if exit_code == 0:
        print("\n" + "=" * 60)
        print("✓ ALL TESTS PASSED")
        print("=" * 60)
    else:
        print("\n" + "=" * 60)
        print("✗ TESTS FAILED")
        print("=" * 60)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()