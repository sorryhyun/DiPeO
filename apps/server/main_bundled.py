#!/usr/bin/env python3
"""
Entry point for the bundled DiPeO server executable.
This wrapper handles path differences when running as a PyInstaller bundle.
"""

import os
import sys
from pathlib import Path


def setup_bundled_paths():
    """Set up paths for the bundled application."""
    # When frozen, PyInstaller sets this attribute
    if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
        # Running as a bundled executable
        bundle_dir = Path(sys._MEIPASS)

        # Set up environment variable for bundled mode
        os.environ["DIPEO_BUNDLED"] = "1"

        # Ensure the data directories exist relative to the executable
        exe_dir = Path(sys.executable).parent

        # Create necessary directories
        files_dir = exe_dir / "files"
        files_dir.mkdir(exist_ok=True)

        for subdir in [
            "uploads",
            "results",
            "conversation_logs",
            "prompts",
            "diagrams",
        ]:
            (files_dir / subdir).mkdir(exist_ok=True)

        # Create .data directory for database
        data_dir = exe_dir / ".data"
        data_dir.mkdir(exist_ok=True)

        # Set the BASE_DIR for the application
        os.environ["DIPEO_BASE_DIR"] = str(exe_dir)

        # Debug logging
        print(f"[BUNDLED] Executable directory: {exe_dir}")
        print(f"[BUNDLED] DIPEO_BASE_DIR set to: {os.environ['DIPEO_BASE_DIR']}")
        print(
            f"[BUNDLED] Expected database path: {exe_dir / '.data' / 'dipeo_state.db'}"
        )

        # Add the bundled packages to Python path
        sys.path.insert(0, str(bundle_dir))

        # Change to the executable directory
        os.chdir(exe_dir)
        print(f"[BUNDLED] Changed working directory to: {Path.cwd()}")


if __name__ == "__main__":
    # Set up bundled paths BEFORE any imports that might use them
    setup_bundled_paths()

    # NOW import the main server after paths are set
    import main

    # Check if main has a start function, otherwise run it directly
    if hasattr(main, "start"):
        main.start()
    else:
        # If there's no start function, the server initialization happens at import time
        # or we need to call the appropriate function
        import uvicorn

        from main import app

        # Get port from environment or use default
        port = int(os.environ.get("PORT", "8000"))
        host = os.environ.get("HOST", "0.0.0.0")

        uvicorn.run(app, host=host, port=port)
