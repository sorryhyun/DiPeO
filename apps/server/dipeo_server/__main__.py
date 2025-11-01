"""Entry point for dipeo-server when run as a module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from main import start


def main():
    """Main entry point for dipeo-server."""
    start()


if __name__ == "__main__":
    main()
