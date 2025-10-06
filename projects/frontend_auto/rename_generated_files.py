#!/usr/bin/env python3
"""
Rename generated temp_section_*.tsx files to their proper names based on sections_data.json
"""

import json
import os
from pathlib import Path


def rename_generated_files(inputs):
    dipeo_base = os.environ.get("DIPEO_BASE_DIR")
    if dipeo_base:
        project_dir = Path(dipeo_base) / "projects" / "frontend_auto"
    else:
        project_dir = Path(__file__).parent

    sections_file = project_dir / "generated" / "sections_data.json"
    if not sections_file.exists():
        print(f"Error: {sections_file} not found")
        return

    with sections_file.open() as f:
        data = json.load(f)

    file_paths = data.get("file_paths", [])
    generated_dir = project_dir / "generated"

    renamed_count = 0
    for i, file_path in enumerate(file_paths):
        temp_file = generated_dir / f"temp_section_{i}.tsx"

        if temp_file.exists():
            target_filename = file_path

            clean_filename = (
                target_filename.replace("src/", "", 1)
                if target_filename.startswith("src/")
                else target_filename
            )
            final_path = generated_dir / "src" / clean_filename

            final_path.parent.mkdir(parents=True, exist_ok=True)

            with temp_file.open() as f:
                lines = f.readlines()

            if lines and lines[0].strip().startswith("```"):
                lines = lines[1:]

            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]

            with final_path.open("w") as f:
                f.writelines(lines)

            temp_file.unlink()

            print(f"✓ Processed temp_section_{i}.tsx -> src/{clean_filename} (removed backticks)")
            renamed_count += 1
        else:
            print(f"⚠ temp_section_{i}.tsx not found, skipping")

    print(f"\n✅ Renamed {renamed_count} files")


if __name__ == "__main__":
    dummy = 1
    rename_generated_files(dummy)
