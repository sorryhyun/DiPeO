# Claude Code SDK --setting-sources Flag Compatibility Issue

## Summary
The `claude-code-sdk` v0.0.23 has a compatibility issue with newer versions of the Claude Code CLI. The SDK always adds the `--setting-sources` flag to the CLI command even when the value is `None` or an empty list, but newer CLI versions don't recognize this flag, causing execution to fail.

## Environment
- **SDK Version**: claude-code-sdk v0.0.23
- **Python Version**: 3.13
- **Claude Code CLI**: Latest version (doesn't support `--setting-sources` flag)

## Problem Description
In `/claude_code_sdk/_internal/transport/subprocess_cli.py`, the `_build_command` method always adds the `--setting-sources` flag:

```python
# Lines 175-180 in subprocess_cli.py
sources_value = (
    ",".join(self._options.setting_sources)
    if self._options.setting_sources is not None
    else ""
)
cmd.extend(["--setting-sources", sources_value])  # Always added!
```

This causes the following error when running with newer CLI versions:
```
error: unknown option '--setting-sources'
Fatal error in message reader: Command failed with exit code 1
```

## Impact
Any application using `claude-code-sdk` with the latest Claude Code CLI will fail to execute queries. This affects:
- Session pooling functionality
- Memory selection operations
- Direct execution mode
- All Claude Code adapter functionality in DiPeO

## Workaround
We've implemented a runtime patch in `/dipeo/infrastructure/llm/providers/claude_code/sdk_patches.py`:

```python
def patch_subprocess_transport():
    """Patch SubprocessCLITransport to handle --setting-sources flag issue."""
    # Monkey-patches the _build_command method to remove empty --setting-sources flag
    # Applied automatically when importing the claude_code provider
```

This patch:
1. Intercepts the command building process
2. Removes `--setting-sources` flag when the value is empty or None
3. Ensures compatibility with newer CLI versions

## Reproduction Steps
1. Install `claude-code-sdk==0.0.23`
2. Install latest Claude Code CLI
3. Create a ClaudeCodeOptions instance without setting `setting_sources`
4. Try to execute any query
5. Observe the "unknown option '--setting-sources'" error

## Suggested Fix for SDK
The SDK should conditionally add the `--setting-sources` flag only when it has a non-empty value:

```python
# Suggested fix in subprocess_cli.py
if self._options.setting_sources:
    sources_value = ",".join(self._options.setting_sources)
    cmd.extend(["--setting-sources", sources_value])
```

Or check if the CLI version supports this flag before adding it.

## Related Files
- `/dipeo/infrastructure/llm/providers/claude_code/sdk_patches.py` - Workaround implementation
- `/dipeo/infrastructure/llm/providers/claude_code/__init__.py` - Patch application
- `.venv/lib/python3.13/site-packages/claude_code_sdk/_internal/transport/subprocess_cli.py` - SDK bug location

## Status
- **Workaround Status**: ✅ Implemented and tested
- **SDK Fix Status**: ⏳ Pending (needs to be fixed in claude-code-sdk repository)
- **DiPeO Impact**: Mitigated with runtime patch
