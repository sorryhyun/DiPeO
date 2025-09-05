"""Platform-specific utilities for TypeScript parser execution."""

import os
import platform
import shutil
from pathlib import Path


def get_tsx_command(project_root: Path) -> list[str]:
    """Get the appropriate command to run TypeScript files via tsx.

    Args:
        project_root: The project root directory

    Returns:
        Command list to execute tsx

    Raises:
        RuntimeError: If no suitable TypeScript runner is found
    """
    if platform.system() == "Windows":
        return _get_windows_tsx_command(project_root)
    else:
        return _get_unix_tsx_command()


def _get_unix_tsx_command() -> list[str]:
    """Get tsx command for Unix-like systems (Linux, macOS).

    Returns:
        Command list starting with 'pnpm tsx'
    """
    return ["pnpm", "tsx"]


def _get_windows_tsx_command(project_root: Path) -> list[str]:
    """Get tsx command for Windows systems.

    Tries multiple strategies to find a working TypeScript runner:
    1. pnpm.CMD or pnpm in PATH
    2. Common pnpm installation locations
    3. npx.CMD or npx as fallback
    4. Direct node with tsx from node_modules

    Args:
        project_root: The project root directory for finding node_modules

    Returns:
        Command list to execute tsx

    Raises:
        RuntimeError: If no suitable runner is found
    """
    # Strategy 1: Try pnpm in PATH
    pnpm_cmd = _find_pnpm_command()
    if pnpm_cmd:
        return [pnpm_cmd, "tsx"]

    # Strategy 2: Try npx as fallback
    npx_cmd = _find_npx_command()
    if npx_cmd:
        return [npx_cmd, "tsx"]

    # Strategy 3: Try node directly with tsx from node_modules
    node_cmd = _find_node_with_tsx(project_root)
    if node_cmd:
        return node_cmd

    raise RuntimeError(
        "Could not find pnpm, npx, or tsx to run TypeScript parser. "
        "Please ensure Node.js and pnpm are installed and in PATH."
    )


def _find_pnpm_command() -> str | None:
    """Find pnpm command on Windows.

    Returns:
        Path to pnpm command or None if not found
    """
    # Try pnpm.CMD first (standard Windows installation)
    if shutil.which("pnpm.CMD"):
        return "pnpm.CMD"

    # Try pnpm without extension
    if shutil.which("pnpm"):
        return "pnpm"

    # Try common installation locations
    common_paths = [
        os.path.expanduser("~\\AppData\\Local\\pnpm\\pnpm.CMD"),
        os.path.expanduser("~\\AppData\\Roaming\\npm\\pnpm.CMD"),
        "C:\\Program Files\\nodejs\\pnpm.CMD",
        "C:\\Program Files (x86)\\nodejs\\pnpm.CMD",
    ]

    for path in common_paths:
        if os.path.exists(path):
            return path

    return None


def _find_npx_command() -> str | None:
    """Find npx command on Windows as fallback.

    Returns:
        Path to npx command or None if not found
    """
    if shutil.which("npx.CMD"):
        return "npx.CMD"

    if shutil.which("npx"):
        return "npx"

    return None


def _find_node_with_tsx(project_root: Path) -> list[str] | None:
    """Find node command with tsx from node_modules.

    Args:
        project_root: Project root directory

    Returns:
        Command list with node and tsx path, or None if not found
    """
    node_cmd = shutil.which("node") or "node"

    # Try to find tsx in node_modules
    tsx_path = project_root / "node_modules" / ".bin" / "tsx"
    if not tsx_path.exists():
        # Try Windows-specific tsx.CMD
        tsx_path = project_root / "node_modules" / ".bin" / "tsx.CMD"

    if tsx_path.exists():
        return [node_cmd, str(tsx_path)]

    return None


def setup_github_actions_env(env: dict[str, str]) -> dict[str, str]:
    """Setup environment for GitHub Actions if needed.

    In GitHub Actions, we need to add paths from GITHUB_PATH to the PATH
    environment variable for subprocess calls.

    Args:
        env: Current environment dictionary

    Returns:
        Updated environment dictionary
    """
    if "GITHUB_ACTIONS" not in env:
        return env

    github_path = env.get("GITHUB_PATH", "")
    if github_path and os.path.exists(github_path):
        try:
            with open(github_path) as f:
                additional_paths = f.read().strip().split("\n")
                current_path = env.get("PATH", "")
                env["PATH"] = os.pathsep.join([*additional_paths, current_path])
        except Exception:
            # If we can't read GITHUB_PATH, just continue with original env
            pass

    return env
