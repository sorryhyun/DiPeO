#!/usr/bin/env python3
"""
Batch generate code for all node specifications using the diagram-based approach.
"""

import sys
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from files.codegen.code.codegen import generate_all_nodes

if __name__ == "__main__":
    # Run batch generation
    result = generate_all_nodes({})
    
    # Exit with error code if any failures
    sys.exit(len(result.get('failed', [])))