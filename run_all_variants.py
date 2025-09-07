#!/usr/bin/env python3
"""
Script to run consolidated_generator for all config files in variants directory
and zip the src/ directory after each generation.
"""

import json
import os
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path


def create_zip(source_dir, zip_name):
    """Create a zip file of the source directory."""
    with zipfile.ZipFile(zip_name, "w", zipfile.ZIP_DEFLATED) as zipf:
        for root, _dirs, files in os.walk(source_dir):
            for file in files:
                file_path = Path(root) / file
                arcname = os.path.relpath(file_path, source_dir)
                zipf.write(file_path, arcname)
    print(f"✓ Created zip: {zip_name}")


def run_variant(config_file):
    """Run dipeo command for a specific config file."""
    config_name = Path(config_file).stem
    print(f"\n{'='*60}")
    print(f"Running variant: {config_name}")
    print(f"Config file: {config_file}")
    print(f"{'='*60}")

    # Prepare the dipeo command
    input_data = json.dumps({"config_file": config_file})
    cmd = [
        "dipeo",
        "run",
        "projects/frontend_auto/consolidated_generator",
        "--light",
        "--debug",
        "--timeout=5400",
        "--input-data",
        input_data,
    ]

    print(f"Command: {' '.join(cmd)}")

    try:
        # Run the command (without capturing output so it streams to console)
        result = subprocess.run(cmd)

        if result.returncode == 0:
            print(f"✓ Successfully ran {config_name}")
        else:
            print(f"✗ Error running {config_name}")

        # Create zip regardless of success/failure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"src_{config_name}_{timestamp}.zip"

        # Check if src directory exists in generated folder
        src_dir = "projects/frontend_auto/generated/src"
        if Path(src_dir).exists():
            create_zip(src_dir, zip_filename)
            # Delete the src directory after zipping
            shutil.rmtree(src_dir)
            print(f"✓ Deleted {src_dir} after zipping")
        else:
            print(f"⚠ Warning: {src_dir} directory not found, skipping zip creation")

        return result.returncode == 0

    except Exception as e:
        print(f"✗ Exception running {config_name}: {e}")
        return False


def main():
    """Main function to process all variant configs."""
    variants_dir = Path("projects/frontend_auto/variants")

    if not variants_dir.exists():
        print(f"Error: Variants directory not found: {variants_dir}")
        return 1

    # Get all JSON config files
    config_files = sorted(variants_dir.glob("*.json"))

    if not config_files:
        print(f"No config files found in {variants_dir}")
        return 1

    print(f"Found {len(config_files)} config files:")
    for cf in config_files:
        print(f"  - {cf.name}")

    # Track results
    results = {}

    # Process each config file
    for config_file in config_files:
        success = run_variant(str(config_file))
        results[config_file.name] = "✓ Success" if success else "✗ Failed"

    # Print summary
    print(f"\n{'='*60}")
    print("SUMMARY")
    print(f"{'='*60}")
    for config_name, status in results.items():
        print(f"{status} - {config_name}")

    # Count successes
    successes = sum(1 for s in results.values() if "Success" in s)
    print(f"\nCompleted: {successes}/{len(results)} successful")

    return 0 if successes == len(results) else 1


if __name__ == "__main__":
    exit(main())
