# TODO Format Guide & Examples

Detailed format templates and examples for comprehensive TODO management.

## Comprehensive Phase-Based Format

```markdown
# DiPeO Project Todos

## [Project Name] (Priority Level)

**Goal**: One-sentence description of what we're accomplishing

**Context**: Why this work is needed and what problem it solves

**Target**: What the end state looks like

### Phase 1: [Phase Name] ([Estimated Effort])
[Brief description of this phase's purpose and deliverables]

- [ ] [Task description starting with action verb]
  - [Detail about implementation approach]
  - [Acceptance criteria or success metrics]
  - Estimated effort: [Small/Medium/Large/Very Large]
  - Files: [Key files that will be modified]
  - Dependencies: [If any prerequisites]
  - Risk: [Low/Medium/High if applicable]

- [ ] [Another task]
  - [Details...]
  - Estimated effort: Medium (2-3 hours)
  - Files: `path/to/file.py`, `path/to/another.py`

### Phase 2: [Phase Name] ([Estimated Effort])
[Description...]

- [ ] [Tasks...]

### Phase 3: [Phase Name] ([Estimated Effort])
[Description...]

- [ ] [Tasks...]

---

## Summary
**Total estimated effort**: [X-Y hours/days]
**Total tasks**: [N tasks across M phases]
**Primary files affected**:
- `file1.py` (major updates)
- `file2.py` (minor cleanup)
- `docs/guide.md` (updates)

**Dependencies**: [List any external blockers]
**Risk**: [Low/Medium/High] - [Brief explanation]
**Mitigation**: [How to reduce risk]
```

## Simpler Format (Quick Tasks)

Only use for simple projects with <5 tasks:

```markdown
# DiPeO Project Todos

## [Project Name]
- [ ] Task 1
- [ ] Task 2
- [ ] Task 3
```

## Full Example: MCP SDK Migration

### ✅ Good Example (Comprehensive)

```markdown
# DiPeO Project Todos

## MCP SDK Migration (High Priority)

**Goal**: Fully migrate from legacy MCP implementation to official SDK

**Context**: Currently running dual implementations (legacy + SDK incomplete)

**Target**: SDK-only with HTTP JSON-RPC transport, backward compatible

### Phase 1: Investigation (2-3 hours)
Understand SDK capabilities and determine migration strategy

- [ ] Investigate MCP SDK v1.16.0 HTTP transport support
  - Check if native HTTP JSON-RPC available (not just SSE)
  - Review mcp.server module documentation
  - Document SDK limitations vs legacy
  - Estimated effort: Small (1-2 hours)
  - Files: N/A (research only)

- [ ] Determine HTTP transport strategy
  - Option A: SDK built-in HTTP (if available)
  - Option B: Custom HTTP wrapper
  - Option C: HTTP JSON-RPC handler delegating to SDK
  - Document decision and rationale
  - Estimated effort: Small (1 hour)
  - Files: Design doc or comments

### Phase 2: Core Implementation (5-7 hours)
Build SDK integration with backward compatibility

- [ ] Enable SDK integration in mcp_sdk_server.py
  - Implement FastAPI integration properly
  - Create /mcp/messages endpoint (HTTP POST, backward compatible)
  - Ensure authentication middleware works
  - Test tool execution via HTTP POST
  - Estimated effort: Medium (3-4 hours)
  - Files: `apps/server/src/dipeo_server/api/mcp_sdk_server.py`
  - Risk: Medium - breaking changes if endpoint URL changes

- [ ] Implement tool registration with SDK
  - Register dipeo_run tool using @server.tool decorator
  - Implement dipeo_list_diagrams tool
  - Ensure all tool parameters properly typed
  - Estimated effort: Medium (2-3 hours)
  - Files: `mcp_sdk_server.py`

### Phase 3: Integration & Testing (3-4 hours)
Validate SDK implementation works end-to-end

- [ ] Test SDK server with Claude Desktop
  - Configure Claude Desktop to use SDK endpoint
  - Test dipeo_run execution
  - Test dipeo_list_diagrams
  - Verify error handling
  - Estimated effort: Medium (2-3 hours)
  - Files: N/A (testing)
  - Dependencies: Phase 2 complete

- [ ] Compare SDK vs legacy behavior
  - Document any differences
  - Ensure backward compatibility
  - Estimated effort: Small (1 hour)

### Phase 4: Cleanup (2-3 hours)
Remove legacy implementation

- [ ] Remove legacy MCP server code
  - Delete `mcp_server.py`
  - Remove legacy routes from router
  - Clean up imports
  - Estimated effort: Small (1-2 hours)
  - Files: `mcp_server.py` (delete), `router.py`
  - Risk: Low

- [ ] Update configuration
  - Remove legacy config options
  - Update environment variables if needed
  - Estimated effort: Small (30 min)
  - Files: Config files

### Phase 5: Documentation & Validation (2-3 hours)
Update docs and final validation

- [ ] Update MCP documentation
  - Update setup instructions
  - Document new endpoint behavior
  - Update examples
  - Estimated effort: Medium (2 hours)
  - Files: `docs/features/mcp-server-integration.md`

- [ ] Final validation
  - Test all MCP tools
  - Verify ngrok integration still works
  - Test with real Claude Desktop client
  - Estimated effort: Small (1 hour)

---

## Summary
**Total estimated effort**: 14-18 hours
**Total tasks**: 12 tasks across 5 phases
**Primary files affected**:
- `mcp_sdk_server.py` (major updates)
- `router.py` (minor cleanup)
- `mcp_server.py` (delete)
- `docs/features/mcp-server-integration.md` (updates)

**Dependencies**: None - can proceed immediately
**Risk**: Medium - potential breaking changes for existing clients
**Mitigation**: Maintain /mcp/messages endpoint URL for backward compatibility
```

### ❌ Bad Example (Not Comprehensive)

```markdown
# DiPeO Project Todos

## MCP Migration
- [ ] Use SDK
- [ ] Remove old code
- [ ] Update docs
```

**Problems**:
- No phases or organization
- No effort estimates
- No file references
- No acceptance criteria
- No summary or context
- Tasks too vague

## Phase Organization Principles

**Group by dependencies and logical workflow:**

- **Phase 1**: Foundation/High Priority - immediate work with high impact
- **Phase 2**: Structural Improvements - medium priority architectural work
- **Phase 3**: Polish & Consistency - standardization and documentation
- **Phase 4**: Future Improvements - low priority enhancements

**Key principles**:
- Group by dependencies and logical workflow
- Each phase should have clear focus and estimated effort
- Remove completed tasks to keep file focused
- Maintain phase structure when adding new tasks
- Avoid scattered, unorganized lists

## Task Details Template

For each task:
```markdown
- [ ] [Action verb] [what to do]
  - [Implementation detail 1]
  - [Implementation detail 2]
  - Estimated effort: [Small/Medium/Large] ([X-Y hours])
  - Files: `path/to/file.py`, `another/file.ts`
  - Dependencies: [What must be done first, if any]
  - Risk: [Low/Medium/High] - [brief explanation]
  - Acceptance criteria: [How to know it's done]
```

## Effort Estimation Guidelines

**Small**: 1-2 hours
- Simple changes
- Minor updates
- Quick fixes

**Medium**: 2-4 hours
- Feature implementation
- Moderate refactoring
- Integration work

**Large**: 4-8 hours
- Complex features
- Major refactoring
- System integration

**Very Large**: 8+ hours
- Consider breaking into multiple tasks
- Multi-day work
- Major architectural changes

## Risk Assessment

**Low Risk**:
- Well-understood changes
- Isolated impact
- Easy to rollback

**Medium Risk**:
- Potential breaking changes
- Multiple integration points
- Requires careful testing

**High Risk**:
- Breaking changes for users
- Complex dependencies
- Limited rollback options
- Requires extensive validation

## Summary Section Template

```markdown
---

## Summary
**Total estimated effort**: [X-Y hours/days]
**Total tasks**: [N tasks across M phases]
**Primary files affected**:
- `file1.py` (major updates - new features)
- `file2.py` (minor cleanup - refactoring)
- `file3.md` (documentation updates)

**Dependencies**: [External blockers or prerequisites]
**Risk**: [Low/Medium/High] - [Brief explanation]
**Mitigation**: [Steps to reduce risk]
**Target completion**: [Optional timeline]
```

## Best Practices

1. **Action verbs**: Start tasks with verbs (Implement, Test, Update, Refactor)
2. **Specificity**: Clear enough for anyone to understand
3. **File references**: Use backticks for file paths
4. **Effort honesty**: Realistic estimates, not wishful thinking
5. **Risk awareness**: Identify and mitigate risks proactively
6. **Summary communication**: Always report plan back to user
