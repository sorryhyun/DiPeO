"""
Script to write Core Kernel files to disk from generated JSON.
"""

import json
import os
from pathlib import Path
from typing import Dict, Any


def write_kernel_files(kernel_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Write Core Kernel files to the generated directory.
    
    Args:
        kernel_data: Dictionary containing kernel response with files array
        
    Returns:
        Status dictionary with success and file paths written
    """
    try:
        base_dir = Path("projects/frontend_auto/generated/src")
        
        # Ensure base directory exists
        base_dir.mkdir(parents=True, exist_ok=True)
        
        written_files = []
        
        # Write each kernel file
        for file_info in kernel_data.get("files", []):
            file_path = base_dir / file_info["file_path"]
            
            # Create parent directories if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Write the file content
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(file_info["content"])
            
            written_files.append(str(file_path))
            print(f"✓ Written: {file_path}")
        
        # Also save the complete kernel data for reference
        kernel_json_path = Path("projects/frontend_auto/generated/core_kernel_data.json")
        with open(kernel_json_path, 'w', encoding='utf-8') as f:
            json.dump(kernel_data, f, indent=2)
        
        print(f"\n✓ Core Kernel generated: {len(written_files)} files")
        
        return {
            "success": True,
            "files_written": written_files,
            "kernel_data_path": str(kernel_json_path),
            "message": f"Successfully wrote {len(written_files)} core kernel files"
        }
        
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "message": f"Failed to write kernel files: {e}"
        }


if __name__ == "__main__":
    # Test with sample data
    sample_kernel = {
        "overview": "Test kernel",
        "files": [
            {
                "file_path": "core/test.ts",
                "purpose": "Test file",
                "exports": ["testExport"],
                "content": "export const testExport = 'test';"
            }
        ],
        "usage_guidelines": ["Test guideline"]
    }
    
    result = write_kernel_files(sample_kernel)
    print(json.dumps(result, indent=2))