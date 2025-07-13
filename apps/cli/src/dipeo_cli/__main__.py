#!/usr/bin/env python3
import sys
import warnings

warnings.warn(
    "dipeo-cli is deprecated. Please use 'dipeo' instead.\n"
    "See MIGRATION_GUIDE.md for details.",
    DeprecationWarning,
    stacklevel=2,
)

# Import and run minimal CLI
from .minimal_cli import main

sys.exit(main())
