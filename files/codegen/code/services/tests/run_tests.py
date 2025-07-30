#!/usr/bin/env python3
"""Run all service tests."""

import subprocess
import sys
from pathlib import Path

if __name__ == '__main__':
    test_dir = Path(__file__).parent
    
    # Run pytest on this directory
    cmd = [sys.executable, '-m', 'pytest', str(test_dir), '-v', '--tb=short']
    
    print(f"Running tests in {test_dir}")
    result = subprocess.run(cmd)
    
    sys.exit(result.returncode)