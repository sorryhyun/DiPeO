"""Patches for Claude Code SDK compatibility issues.

This module contains patches to work around issues in the Claude Code SDK,
particularly with newer versions of the Claude Code CLI.
"""

import logging

from dipeo.config.base_logger import get_module_logger

logger = get_module_logger(__name__)

def patch_subprocess_transport():
    """Patch SubprocessCLITransport to handle --setting-sources flag issue.

    The SDK v0.0.23 always adds --setting-sources flag even when None/empty,
    but newer CLI versions don't recognize this flag. This patch removes the
    flag when it would be empty.
    """
    try:
        from claude_code_sdk._internal.transport.subprocess_cli import SubprocessCLITransport

        # Save original _build_command method
        original_build_command = SubprocessCLITransport._build_command

        def patched_build_command(self):
            """Patched version that handles setting_sources properly."""
            # Call original method
            cmd = original_build_command(self)

            # Remove --setting-sources flag if it exists with empty value
            if "--setting-sources" in cmd:
                try:
                    idx = cmd.index("--setting-sources")
                    # Check if next item is empty or another flag
                    if idx + 1 < len(cmd):
                        next_val = cmd[idx + 1]
                        if not next_val or next_val.startswith("--"):
                            # Remove the flag and empty value
                            cmd.pop(idx)  # Remove --setting-sources
                            if idx < len(cmd) and not cmd[idx].startswith("--"):
                                cmd.pop(idx)  # Remove empty value
                        elif next_val == "":
                            # Remove flag and empty string value
                            cmd.pop(idx)  # Remove --setting-sources
                            cmd.pop(idx)  # Remove empty string
                except (IndexError, ValueError):
                    pass

            return cmd

        # Replace method
        SubprocessCLITransport._build_command = patched_build_command
        logger.info(
            "[SDK Patch] Successfully patched SubprocessCLITransport for --setting-sources compatibility"
        )

    except Exception as e:
        logger.warning(f"[SDK Patch] Failed to patch SubprocessCLITransport: {e}")

def apply_all_patches():
    """Apply all SDK patches."""
    patch_subprocess_transport()
