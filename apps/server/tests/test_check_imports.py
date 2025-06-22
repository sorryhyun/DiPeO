import subprocess
from pathlib import Path

import pytest


class TestImportLinter:
    """Test to check import violations using import-linter."""

    def test_no_import_violations(self):
        """Ensure no import violations exist in the codebase."""
        # Find the server directory (where .importlinter config is)
        server_dir = Path(__file__).parent.parent

        try:
            result = subprocess.run(
                ["lint-imports"],
                capture_output=True,
                text=True,
                check=False,
                cwd=str(server_dir),  # Run from server directory
            )

            if result.returncode != 0:
                error_msg = "Import violations detected:\n"
                error_msg += result.stdout
                if result.stderr:
                    error_msg += f"\nErrors: {result.stderr}"

                pytest.fail(error_msg)

        except FileNotFoundError:
            pytest.skip(
                "import-linter not installed. Install with: pip install import-linter"
            )
        except Exception as e:
            pytest.fail(f"Error running import-linter: {e}")
