#!/usr/bin/env python3
"""
Rename generated temp_section_*.tsx files to their proper names based on sections_data.json
"""

import json
import os
from pathlib import Path

def rename_generated_files(inputs):
    # Get base directory from environment or use current file's location
    dipeo_base = os.environ.get('DIPEO_BASE_DIR')
    if dipeo_base:
        project_dir = Path(dipeo_base) / "projects" / "frontend_auto"
    else:
        # Fallback to relative path from script location
        project_dir = Path(__file__).parent
    
    # Read sections data
    sections_file = project_dir / "generated" / "sections_data.json"
    if not sections_file.exists():
        print(f"Error: {sections_file} not found")
        return
    
    with open(sections_file, 'r') as f:
        data = json.load(f)
    
    file_paths = data.get('file_paths', [])
    generated_dir = project_dir / "generated"
    
    renamed_count = 0
    for i, file_path in enumerate(file_paths):
        temp_file = generated_dir / f"temp_section_{i}.tsx"
        
        if temp_file.exists():
            target_filename = file_path
            final_path = generated_dir / target_filename
            
            # Create directory if needed
            final_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Read file content and remove backticks from first and last lines
            with open(temp_file, 'r') as f:
                lines = f.readlines()
            
            # Remove backticks from first line if present
            if lines and lines[0].strip().startswith('```'):
                lines = lines[1:]
            
            # Remove backticks from last line if present
            if lines and lines[-1].strip() == '```':
                lines = lines[:-1]
            
            # Write cleaned content to final file
            with open(final_path, 'w') as f:
                f.writelines(lines)
            
            # Remove the temp file
            temp_file.unlink()
            
            print(f"✓ Processed temp_section_{i}.tsx -> {target_filename} (removed backticks)")
            renamed_count += 1
        else:
            print(f"⚠ temp_section_{i}.tsx not found, skipping")
    
    print(f"\n✅ Renamed {renamed_count} files")

if __name__ == "__main__":
    dummy=1
    rename_generated_files(dummy)