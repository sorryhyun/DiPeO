#!/usr/bin/env python3
"""
Check imports using import-linter.

This script runs import-linter to ensure no deep path imports or old imports are used.
Exit with non-zero status if violations are found.
"""

import subprocess
import sys

def main():
    """Run import-linter and exit with appropriate status."""
    print("Running import-linter...")
    
    try:
        result = subprocess.run(
            ["python", "-m", "import_linter"],
            capture_output=True,
            text=True,
            check=False
        )
        
        if result.returncode != 0:
            print("❌ Import violations detected:")
            print(result.stdout)
            if result.stderr:
                print("Errors:", result.stderr)
            sys.exit(1)
        else:
            print("✅ All import checks passed!")
            print(result.stdout)
            
    except FileNotFoundError:
        print("Error: import-linter not installed. Install with: pip install import-linter")
        sys.exit(1)
    except Exception as e:
        print(f"Error running import-linter: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()