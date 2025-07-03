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
    if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
        # Running as a bundled executable
        bundle_dir = Path(sys._MEIPASS)
        
        # Set up environment variable for bundled mode
        os.environ['DIPEO_BUNDLED'] = '1'
        
        # Ensure the data directories exist relative to the executable
        exe_dir = Path(sys.executable).parent
        
        # Create necessary directories
        files_dir = exe_dir / 'files'
        files_dir.mkdir(exist_ok=True)
        
        for subdir in ['uploads', 'results', 'conversation_logs', 'prompts', 'diagrams']:
            (files_dir / subdir).mkdir(exist_ok=True)
        
        # Create .data directory for database
        data_dir = exe_dir / '.data'
        data_dir.mkdir(exist_ok=True)
        
        # Set the BASE_DIR for the application
        os.environ['DIPEO_BASE_DIR'] = str(exe_dir)
        
        # Add the bundled packages to Python path
        sys.path.insert(0, str(bundle_dir))
        
        # Change to the executable directory
        os.chdir(exe_dir)

if __name__ == "__main__":
    # Set up bundled paths if running as executable
    setup_bundled_paths()
    
    # Import and run the main server
    from main import start
    start()