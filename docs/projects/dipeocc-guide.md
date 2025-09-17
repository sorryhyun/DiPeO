# DiPeO CC Project Guide

## Overview

`dipeo_cc` tracks the Claude Code TODO mirroring workstream. The project converts `TodoWrite` payloads emitted by Claude Code hooks into Light diagrams so DiPeO can visualize and monitor in-progress tasks alongside other agent executions.

## Goals

- Capture TODO updates via Claude Code shell hooks without modifying the core SDK.
- Materialize real-time TODO state into diagrams persisted under `projects/dipeo_cc/`.
- Keep DiPeO CLI, monitor UI, and documentation aligned around the new hook-driven flow.

## Project Structure

```
projects/
  dipeo_cc/
    README.md (optional)
    {session_id}.light.yaml  # Generated diagrams per Claude session
```

Runtime artifacts (raw snapshots, logs) continue to land under `.dipeo/workspaces/exec_{trace_id}/`, while reviewed diagrams move into `projects/dipeo_cc/` for replay and collaboration.

## Workplan Alignment

The project follows the phases captured in `TODO.md`:

1. **SDK & Docs Groundwork** – confirm Python SDK capabilities, document hook behavior, and outline design choices for mapping TODOs to `claude-code-custom` person jobs.
2. **Capture TODO Updates** – add hook wiring to `UnifiedClaudeCodeClient`, implement a `TodoTaskCollector`, and persist snapshots.
3. **Translate to Diagrams** – build translators that emit Light diagrams with status-based layouts and doc references.
4. **Live Sync & Execution Integration** – debounce updates, auto-register diagrams for monitoring, and provide toggles for teams.
5. **Web Monitor & UX** – surface TODO diagrams in GraphQL, render custom nodes, and expose raw task lists in the UI.
6. **Automation & Docs** – ship tests, integration smoke runs, and finalize runbooks.

## Development Checklist

- [ ] Enable `PostToolUse` → `TodoWrite` hooks in `UnifiedClaudeCodeClient` or the `claude-code-custom` variant.
- [ ] Serialize incoming payloads into `TodoSnapshot` entries and write them to `.dipeo/workspaces/`.
- [ ] Run the translator to regenerate `projects/dipeo_cc/{session_id}.light.yaml` after each snapshot update.
- [ ] Execute `dipeo run projects/dipeo_cc/{session_id}` to validate diagrams render correctly.
- [ ] Update `doc.md` and `docs/integrations/claude-code.md` once hook collection ships.
- [ ] Add regression coverage (collector parsing, translator output, UI rendering).

## Testing Tips

- Use a minimal shell hook that echoes sample TODO JSON to verify the collector before integrating with live Claude sessions.
- When developing the translator, compare generated diagrams in `projects/dipeo_cc/` against the raw snapshot to ensure column ordering and status colors match expectations.
- Leverage `make dev-server` and `make dev-web` to watch diagrams refresh inside the monitor during live sync experiments.

## Next Steps

- Finalize the Phase 2 collector implementation and land documentation updates that point contributors to this guide.
- Coordinate with design on `todo_task` node visuals so the web UI changes can be staged alongside the translator release.
