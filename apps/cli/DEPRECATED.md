# DEPRECATED

This CLI package has been deprecated and consolidated into the server package.

The CLI functionality is now integrated directly into `apps/server/src/dipeo_server/cli/` for better code reuse and reduced duplication.

## New Location

All CLI commands are now available through the unified entry point in the server package:
- Entry point: `apps/server/src/dipeo_server/cli/entry_point.py`
- CLI runner: `apps/server/src/dipeo_server/cli/cli_runner.py`

## Benefits of Consolidation

1. **No subprocess management**: Direct service calls instead of spawning server process
2. **Better performance**: No HTTP/GraphQL overhead for local operations
3. **Code reuse**: Eliminates duplicate diagram loading and GraphQL client code
4. **Simpler deployment**: Single package for both server and CLI
5. **Reduced maintenance**: ~30% less code to maintain

## Usage

The `dipeo` and `dipeocc` commands work the same as before, but now use direct service calls internally when running CLI commands.