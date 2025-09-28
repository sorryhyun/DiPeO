"""Test script to verify new pipeline-based builders produce compatible output."""

import asyncio
import json
from pathlib import Path
from typing import Any

# Import existing builders
from dipeo.infrastructure.codegen.ir_builders import (
    BackendIRBuilder as OldBackendBuilder,
)
from dipeo.infrastructure.codegen.ir_builders import (
    FrontendIRBuilder as OldFrontendBuilder,
)
from dipeo.infrastructure.codegen.ir_builders import (
    StrawberryIRBuilder as OldStrawberryBuilder,
)

# Import new builders
from dipeo.infrastructure.codegen.ir_builders.builders import (
    BackendBuilder as NewBackendBuilder,
)
from dipeo.infrastructure.codegen.ir_builders.builders import (
    FrontendBuilder as NewFrontendBuilder,
)
from dipeo.infrastructure.codegen.ir_builders.builders import (
    StrawberryBuilder as NewStrawberryBuilder,
)

# Import validators
from dipeo.infrastructure.codegen.ir_builders.validators import get_validator


def load_test_ast() -> dict[str, Any]:
    """Load test AST data from parsed TypeScript files.

    Returns:
        Dictionary of AST data
    """
    # Try to load from the typical location
    ast_path = Path("projects/codegen/parsed/typescript_ast.json")
    if ast_path.exists():
        with open(ast_path) as f:
            return json.load(f)

    # If not found, return minimal test data
    print("Warning: Could not find typescript_ast.json, using minimal test data")
    return {"test_file": {"type": "module", "body": []}}


async def test_backend_builder():
    """Test backend builder compatibility."""
    print("\n=== Testing Backend Builder ===")

    ast_data = load_test_ast()

    # Test old builder
    print("Testing old backend builder...")
    old_builder = OldBackendBuilder()
    old_result = await old_builder.build_ir(ast_data)

    # Test new builder
    print("Testing new backend builder...")
    new_builder = NewBackendBuilder()
    new_result = await new_builder.build_ir(ast_data)

    # Validate with new validator
    validator = get_validator("backend")
    validation = validator.validate(new_result.data)

    print(f"Old builder result keys: {list(old_result.data.keys())}")
    print(f"New builder result keys: {list(new_result.data.keys())}")
    print(f"Validation: {validation.get_summary()}")

    # Check key compatibility
    old_keys = set(old_result.data.keys())
    new_keys = set(new_result.data.keys())

    missing_keys = old_keys - new_keys
    extra_keys = new_keys - old_keys

    if missing_keys:
        print(f"⚠️  Missing keys in new builder: {missing_keys}")
    if extra_keys:
        print(f"ℹ️  Extra keys in new builder: {extra_keys}")

    # Save outputs for comparison
    output_dir = Path("projects/codegen/ir/test_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "backend_old.json", "w") as f:
        json.dump(old_result.data, f, indent=2, default=str)

    with open(output_dir / "backend_new.json", "w") as f:
        json.dump(new_result.data, f, indent=2, default=str)

    print(f"✅ Backend builder test complete. Outputs saved to {output_dir}")

    # Print validation errors if any
    if validation.errors:
        print("\nValidation errors:")
        for error in validation.errors[:5]:  # Show first 5 errors
            print(f"  - {error}")

    if validation.warnings:
        print("\nValidation warnings:")
        for warning in validation.warnings[:5]:  # Show first 5 warnings
            print(f"  - {warning}")

    return validation.is_valid


async def test_frontend_builder():
    """Test frontend builder compatibility."""
    print("\n=== Testing Frontend Builder ===")

    ast_data = load_test_ast()

    # Test old builder
    print("Testing old frontend builder...")
    old_builder = OldFrontendBuilder()
    old_result = await old_builder.build_ir(ast_data)

    # Test new builder
    print("Testing new frontend builder...")
    new_builder = NewFrontendBuilder()
    new_result = await new_builder.build_ir(ast_data)

    # Validate with new validator
    validator = get_validator("frontend")
    validation = validator.validate(new_result.data)

    print(f"Old builder result keys: {list(old_result.data.keys())}")
    print(f"New builder result keys: {list(new_result.data.keys())}")
    print(f"Validation: {validation.get_summary()}")

    # Check key compatibility
    old_keys = set(old_result.data.keys())
    new_keys = set(new_result.data.keys())

    missing_keys = old_keys - new_keys
    extra_keys = new_keys - old_keys

    if missing_keys:
        print(f"⚠️  Missing keys in new builder: {missing_keys}")
    if extra_keys:
        print(f"ℹ️  Extra keys in new builder: {extra_keys}")

    # Save outputs for comparison
    output_dir = Path("projects/codegen/ir/test_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "frontend_old.json", "w") as f:
        json.dump(old_result.data, f, indent=2, default=str)

    with open(output_dir / "frontend_new.json", "w") as f:
        json.dump(new_result.data, f, indent=2, default=str)

    print(f"✅ Frontend builder test complete. Outputs saved to {output_dir}")

    # Print validation errors if any
    if validation.errors:
        print("\nValidation errors:")
        for error in validation.errors[:5]:  # Show first 5 errors
            print(f"  - {error}")

    if validation.warnings:
        print("\nValidation warnings:")
        for warning in validation.warnings[:5]:  # Show first 5 warnings
            print(f"  - {warning}")

    return validation.is_valid


async def test_strawberry_builder():
    """Test Strawberry builder compatibility."""
    print("\n=== Testing Strawberry Builder ===")

    ast_data = load_test_ast()

    # Test old builder
    print("Testing old strawberry builder...")
    old_builder = OldStrawberryBuilder()
    old_result = await old_builder.build_ir(ast_data)

    # Test new builder
    print("Testing new strawberry builder...")
    new_builder = NewStrawberryBuilder()
    new_result = await new_builder.build_ir(ast_data)

    # Validate with new validator
    validator = get_validator("strawberry")
    validation = validator.validate(new_result.data)

    print(f"Old builder result keys: {list(old_result.data.keys())}")
    print(f"New builder result keys: {list(new_result.data.keys())}")
    print(f"Validation: {validation.get_summary()}")

    # Check key compatibility
    old_keys = set(old_result.data.keys())
    new_keys = set(new_result.data.keys())

    missing_keys = old_keys - new_keys
    extra_keys = new_keys - old_keys

    if missing_keys:
        print(f"⚠️  Missing keys in new builder: {missing_keys}")
    if extra_keys:
        print(f"ℹ️  Extra keys in new builder: {extra_keys}")

    # Save outputs for comparison
    output_dir = Path("projects/codegen/ir/test_outputs")
    output_dir.mkdir(parents=True, exist_ok=True)

    with open(output_dir / "strawberry_old.json", "w") as f:
        json.dump(old_result.data, f, indent=2, default=str)

    with open(output_dir / "strawberry_new.json", "w") as f:
        json.dump(new_result.data, f, indent=2, default=str)

    print(f"✅ Strawberry builder test complete. Outputs saved to {output_dir}")

    # Print validation errors if any
    if validation.errors:
        print("\nValidation errors:")
        for error in validation.errors[:5]:  # Show first 5 errors
            print(f"  - {error}")

    if validation.warnings:
        print("\nValidation warnings:")
        for warning in validation.warnings[:5]:  # Show first 5 warnings
            print(f"  - {warning}")

    return validation.is_valid


async def main():
    """Run all builder tests."""
    print("=" * 60)
    print("Testing New Pipeline-Based IR Builders")
    print("=" * 60)

    # Run all tests
    backend_valid = await test_backend_builder()
    frontend_valid = await test_frontend_builder()
    strawberry_valid = await test_strawberry_builder()

    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    print(f"Backend Builder: {'✅ VALID' if backend_valid else '❌ INVALID'}")
    print(f"Frontend Builder: {'✅ VALID' if frontend_valid else '❌ INVALID'}")
    print(f"Strawberry Builder: {'✅ VALID' if strawberry_valid else '❌ INVALID'}")

    if all([backend_valid, frontend_valid, strawberry_valid]):
        print("\n🎉 All builders validated successfully!")
        print("\nNext steps:")
        print("1. Compare the output files in projects/codegen/ir/test_outputs/")
        print("2. Run 'make codegen' to test the full pipeline")
        print("3. If successful, update ir_registry.py to use new builders")
    else:
        print("\n⚠️  Some builders have validation issues. Please review the errors above.")

    return all([backend_valid, frontend_valid, strawberry_valid])


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)
