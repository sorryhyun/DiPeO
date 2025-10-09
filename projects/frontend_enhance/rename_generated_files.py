#!/usr/bin/env python3
"""Rename generated temp_section_*.tsx files to their proper names based on sections_data.json"""

import json
import os
import shutil
from pathlib import Path


def rename_generated_files(inputs):
    dipeo_base = os.environ.get("DIPEO_BASE_DIR")
    if dipeo_base:
        project_dir = Path(dipeo_base) / "projects" / "frontend_enhance"
    else:
        project_dir = Path(__file__).parent

    sections_file = project_dir / "generated" / "sections_data.json"
    if not sections_file.exists():
        print(f"Error: {sections_file} not found")
        return

    with sections_file.open() as f:
        data = json.load(f)

    sections = data.get("sections", [])
    generated_dir = project_dir / "generated"

    renamed_count = 0
    for i, section in enumerate(sections):
        temp_file = generated_dir / f"temp_section_{i}.tsx"

        if temp_file.exists():
            target_filename = section.get("file_to_implement", f"section_{i}.tsx")
            final_path = generated_dir / target_filename

            final_path.parent.mkdir(parents=True, exist_ok=True)

            shutil.move(str(temp_file), str(final_path))
            print(f"✓ Renamed temp_section_{i}.tsx -> {target_filename}")
            renamed_count += 1
        else:
            print(f"⚠ temp_section_{i}.tsx not found, skipping")

    print(f"\n✅ Renamed {renamed_count} files")


if __name__ == "__main__":
    dummy = 1
    rename_generated_files(dummy)
