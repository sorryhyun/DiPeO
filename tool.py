#!/usr/bin/env python3
"""
DiPeO CLI Tool - Simplified wrapper

This is a lightweight wrapper that delegates to the actual CLI implementation
in the dipeo_cli package. This ensures the CLI is fully decoupled from server
internals.
"""

import sys
import os

# Add CLI package to path for development
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'cli'))

try:
    from dipeo_cli.__main__ import main
except ImportError:
    print("Error: DiPeO CLI package not found.")
    print("Please ensure the CLI package is installed:")
    print("  cd cli && pip install -e .")
    sys.exit(1)

if __name__ == "__main__":
    main()