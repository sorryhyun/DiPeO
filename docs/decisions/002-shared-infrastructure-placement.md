# ADR 002: Shared Infrastructure Placement for CLI/Server Separation

**Status**: Accepted
**Date**: 2025-11-01
**Context**: CLI/Server separation migration

## Decision

Move `apps/server/dipeo_server/infra/message_store.py` to `/dipeo/infrastructure/storage/message_store.py`.

## Context

During the CLI/Server separation, we identified that `message_store.py` is shared infrastructure used by both:
- **CLI**: Stores execution results, messages, and transitions
- **Server**: Queries execution data for GraphQL API

We evaluated three options for placing this shared code:

### Option A: Move to dipeo/infrastructure/storage/ (CHOSEN)
**Pros:**
- ✅ Architectural consistency - Message store is infrastructure, belongs in core library
- ✅ Correct dependency direction - Both CLI and server depend on dipeo, not each other
- ✅ Reusability - Future consumers (tests, tools) can access without server dependency
- ✅ Conceptual clarity - Message persistence is a core capability, not server-specific
- ✅ Existing location - `/dipeo/infrastructure/storage/` already exists with similar implementations

**Cons:**
- Minor: Requires updating imports in both CLI and server code

### Option B: Keep in /server/infra/, CLI imports from server
**Pros:**
- Minimal file movement

**Cons:**
- ❌ Creates dependency from CLI → server (wrong direction)
- ❌ Can't use CLI without installing server package
- ❌ Violates separation of concerns
- ❌ Confusing conceptual model (why is CLI importing from server?)

### Option C: Create /shared/ package at root
**Pros:**
- Clear "shared" designation

**Cons:**
- ❌ Creates new top-level package for single file
- ❌ Doesn't leverage existing infrastructure organization
- ❌ Less discoverable than standard infrastructure location

## Decision Rationale

Option A provides the best architectural alignment:

1. **Dependency direction**: Maintains proper dependency flow (CLI → dipeo ← Server)
2. **Location consistency**: Fits naturally with existing storage implementations in `/dipeo/infrastructure/storage/`
3. **Conceptual clarity**: Message store is infrastructure, not application logic
4. **Reusability**: Any future component can access message store through core library

## Implementation

### New Location
```
/dipeo/infrastructure/storage/message_store.py
```

### Import Path
```python
from dipeo.infrastructure.storage.message_store import MessageStore
```

### Files to Update
1. CLI files importing MessageStore (search in cli/)
2. Server files importing MessageStore (search in api/)
3. Bootstrap/wiring code
4. Export from `/dipeo/infrastructure/storage/__init__.py`

## Consequences

**Positive:**
- Clear architectural boundaries
- Reusable infrastructure component
- No circular dependencies
- Easier to test and maintain

**Negative:**
- None identified

## Related
- Migration analysis: `docs/migration-analysis.md`
- TODO: CLI/Server Separation - Option 1a
