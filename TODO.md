# DiPeO Project Todos

## MCP SDK Migration (High Priority)

**Goal**: Fully migrate from legacy MCP implementation to official MCP Python SDK, removing all custom JSON-RPC handling.

**Context**: Currently running dual MCP implementations:
- Legacy: `mcp_server.py` with manual JSON-RPC 2.0 handling
- SDK: `mcp_sdk_server.py` with official SDK but incomplete integration

**Target**: SDK-only implementation with HTTP JSON-RPC transport support

### Phase 1: SDK Investigation & Setup
- [ ] Investigate MCP SDK v1.16.0 HTTP transport capabilities
  - Check if SDK supports HTTP JSON-RPC natively (not just SSE)
  - Review `mcp.server` module for HTTP transport options
  - Document SDK limitations vs legacy implementation
  - Estimated effort: Small (1-2 hours)

- [ ] Determine HTTP transport strategy
  - Option A: Use SDK's built-in HTTP support (if available)
  - Option B: Create custom HTTP wrapper for SDK
  - Option C: Implement HTTP JSON-RPC handler that delegates to SDK
  - Document decision and rationale
  - Estimated effort: Small (1 hour)

### Phase 2: Core SDK Implementation
- [ ] Enable SDK integration in `mcp_sdk_server.py`
  - Uncomment and implement proper SDK FastAPI integration
  - Create HTTP JSON-RPC endpoint at `/mcp/messages` (backward compatible)
  - Ensure authentication works with SDK endpoints
  - Test tool execution via HTTP POST
  - Estimated effort: Medium (3-4 hours)

- [ ] Migrate `/mcp/info` endpoint to SDK router
  - Copy logic from `mcp_server.py:326-388`
  - Integrate with SDK server instance for tool/resource listing
  - Maintain authentication dependency
  - Test response format matches legacy
  - File: `apps/server/src/dipeo_server/api/mcp_sdk_server.py`
  - Estimated effort: Small (1 hour)

- [ ] Migrate OAuth metadata endpoint to SDK router
  - Copy logic from `mcp_server.py:393-414`
  - Ensure `/.well-known/oauth-authorization-server` works
  - Required by MCP spec for authentication discovery
  - Test metadata response
  - File: `apps/server/src/dipeo_server/api/mcp_sdk_server.py`
  - Estimated effort: Small (30 min)

### Phase 3: Legacy Removal
- [ ] Remove legacy MCP implementation
  - Delete `apps/server/src/dipeo_server/api/mcp_server.py`
  - Keep `mcp_utils.py` (shared logic)
  - Estimated effort: Small (15 min)

- [ ] Update router configuration
  - Remove `mcp_server` import in `router.py`
  - Remove `app.include_router(mcp_router)` line
  - Ensure only SDK router is registered
  - File: `apps/server/src/dipeo_server/api/router.py`
  - Estimated effort: Small (15 min)

### Phase 4: Testing & Validation
- [ ] Test SDK endpoints with authentication
  - Test `/mcp/messages` with JWT bearer token
  - Test `/mcp/messages` with API key
  - Test unauthenticated requests (if MCP_AUTH_REQUIRED=false)
  - Test tool execution (dipeo_run)
  - Test resource listing (dipeo://diagrams)
  - Estimated effort: Medium (2 hours)

- [ ] Test backward compatibility
  - Verify existing curl commands from docs still work
  - Test with Claude Desktop integration
  - Test with ngrok exposure
  - Estimated effort: Medium (2 hours)

### Phase 5: Documentation Updates
- [ ] Update MCP server integration docs
  - Update endpoint URLs in `docs/features/mcp-server-integration.md`
  - Document any SDK-specific behavior changes
  - Update curl examples if needed
  - Remove references to legacy implementation
  - Estimated effort: Medium (2 hours)

- [ ] Update OAuth authentication docs
  - Review `docs/features/mcp-oauth-authentication.md`
  - Ensure SDK authentication flow is documented
  - Update any code examples
  - Estimated effort: Small (1 hour)

- [ ] Update CLAUDE.md if needed
  - Check for MCP endpoint references
  - Update quick start examples
  - Estimated effort: Small (30 min)

---

## Summary
**Total estimated effort**: 14-18 hours
**Primary files affected**:
- `apps/server/src/dipeo_server/api/mcp_sdk_server.py` (major updates)
- `apps/server/src/dipeo_server/api/router.py` (minor cleanup)
- `apps/server/src/dipeo_server/api/mcp_server.py` (delete)
- `docs/features/mcp-server-integration.md` (updates)
- `docs/features/mcp-oauth-authentication.md` (review/updates)

**Dependencies**: None - can proceed immediately
**Risk**: Medium - breaking change for existing MCP clients if endpoints change
**Mitigation**: Maintain `/mcp/messages` endpoint URL for backward compatibility
