# ChatGPT Widgets: Next PR Plan

This document outlines improvements and enhancements to be implemented in follow-up PRs for the ChatGPT apps integration.

## Overview

The initial PR (#192) establishes the foundational infrastructure for ChatGPT widgets. This plan documents critical improvements identified during code review that should be implemented before production deployment.

## Priority 1: Type Safety & Code Generation

### GraphQL Type Generation
**Issue**: Widgets manually define TypeScript interfaces for GraphQL responses instead of using generated types from the schema.

**Current State**:
```typescript
// Manual interface definitions in each widget
interface ExecutionInfo {
  sessionId: string;
  status: Status;
  diagramName: string;
  // ...
}
```

**Target State**:
```typescript
// Use GraphQL Code Generator like main frontend
import { GetExecutionQuery } from '../__generated__/graphql';
```

**Implementation Steps**:
1. Add `@graphql-codegen/cli` to `apps/chatgpt-widgets/package.json`
2. Create `apps/chatgpt-widgets/codegen.ts` configuration
3. Generate types from GraphQL schema at build time
4. Replace manual interfaces with generated types in all widgets
5. Update Makefile targets to run codegen before building widgets

**Benefits**:
- Type safety guaranteed by schema
- Automatic detection of schema changes
- Consistent with main frontend architecture
- Eliminates manual type maintenance

**Files to Modify**:
- `apps/chatgpt-widgets/package.json`
- `apps/chatgpt-widgets/codegen.ts` (new)
- `apps/chatgpt-widgets/src/execution-results/index.tsx`
- `apps/chatgpt-widgets/src/execution-list/index.tsx`
- `apps/chatgpt-widgets/src/diagram-list/index.tsx`
- `Makefile` (add codegen step)

---

## Priority 2: Testing Infrastructure

### Comprehensive Test Suite
**Issue**: PR adds 1338 lines with zero test coverage.

**Minimum Required Coverage**:

#### 1. Custom Hooks Tests
```typescript
// src/hooks/__tests__/use-graphql-query.test.ts
- Should fetch data successfully
- Should handle GraphQL errors
- Should handle network errors
- Should refetch on interval
- Should skip when skip=true
- Should update on variable changes
```

```typescript
// src/hooks/__tests__/use-widget-state.test.ts
- Should get initial state immediately
- Should poll with exponential backoff
- Should stop polling after max attempts
- Should handle missing window.oai object
```

#### 2. GraphQL Client Tests
```typescript
// src/lib/__tests__/graphql-client.test.ts
- Should make successful requests
- Should handle HTTP errors
- Should handle malformed responses
- Should include correct headers
- Should resolve correct server URL
```

#### 3. Component Tests
```typescript
// src/components/__tests__/ErrorBoundary.test.tsx
- Should render children when no error
- Should catch and display errors
- Should log errors to console
```

```typescript
// src/components/__tests__/StatusBadge.test.tsx
- Should render correct color for each status
- Should display status text
```

#### 4. Widget Integration Tests
- Test each widget with mock GraphQL responses
- Test loading states
- Test error states
- Test empty states
- Test refetch functionality

**Implementation Steps**:
1. Add testing dependencies: `vitest`, `@testing-library/react`, `@testing-library/react-hooks`
2. Create test setup file with mock configurations
3. Implement unit tests for all hooks
4. Implement unit tests for GraphQL client
5. Implement component tests
6. Add test npm scripts and Makefile targets
7. Configure CI to run tests

**Files to Create**:
- `apps/chatgpt-widgets/vitest.config.ts`
- `apps/chatgpt-widgets/src/test-setup.ts`
- All test files listed above

---

## Priority 3: Performance Optimizations

### 1. Fix useGraphQLQuery Re-render Issue
**Issue**: `JSON.stringify(variables)` causes unnecessary re-renders.

**Current**:
```typescript
useEffect(() => {
  executeQuery();
}, [query, JSON.stringify(variables), options.skip]);
```

**Solution**:
```typescript
import { useDeepCompareMemoize } from 'use-deep-compare';

useEffect(() => {
  executeQuery();
}, [query, useDeepCompareMemoize(variables), options.skip]);
```

**Files**: `src/hooks/use-graphql-query.ts`

### 2. Add Search Debouncing
**Issue**: Diagram search filters on every keystroke.

**Current**:
```typescript
<input
  value={searchQuery}
  onChange={(e) => setSearchQuery(e.target.value)}
/>
```

**Solution**:
```typescript
// Create custom hook
function useDebouncedValue<T>(value: T, delay: number): T {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => clearTimeout(handler);
  }, [value, delay]);

  return debouncedValue;
}

// Use in component
const [searchQuery, setSearchQuery] = useState('');
const debouncedQuery = useDebouncedValue(searchQuery, 300);

const filteredDiagrams = useMemo(
  () => data?.diagrams?.filter(/* use debouncedQuery */),
  [data, debouncedQuery]
);
```

**Files**:
- `src/hooks/use-debounced-value.ts` (new)
- `src/diagram-list/index.tsx`

### 3. Optimize Refetch Intervals
**Issue**: Aggressive polling intervals may cause excessive API load.

**Current Intervals**:
- execution-list: 10s
- execution-results: 5s

**Considerations**:
1. Implement WebSocket subscriptions for real-time updates (ideal)
2. Increase intervals (30s+) with manual refresh button
3. Pause polling when widget is not visible (Page Visibility API)

**Recommended Approach**:
```typescript
// Use Page Visibility API
useEffect(() => {
  const handleVisibilityChange = () => {
    if (document.hidden) {
      // Pause polling
    } else {
      // Resume polling
      refetch();
    }
  };

  document.addEventListener('visibilitychange', handleVisibilityChange);
  return () => document.removeEventListener('visibilitychange', handleVisibilityChange);
}, [refetch]);
```

**Files**:
- `src/hooks/use-graphql-query.ts`
- `src/execution-results/index.tsx`
- `src/execution-list/index.tsx`

---

## Priority 4: Security Hardening

### 1. Authentication & Authorization
**Issue**: Widgets can query any execution data without authentication.

**Required**:
1. API key authentication for widget requests
2. Scope queries to user-owned data
3. Rate limiting for widget endpoints

**Implementation Strategy**:
```python
# apps/server/src/dipeo_server/api/middleware.py
async def verify_widget_auth(request: Request):
    api_key = request.headers.get("X-Widget-API-Key")
    if not api_key or not verify_api_key(api_key):
        raise HTTPException(status_code=401)
    return get_user_from_key(api_key)

# Add to GraphQL context
@app.post("/graphql")
async def graphql_endpoint(request: Request):
    user = await verify_widget_auth(request)
    context = {"user": user}
    # ...
```

**Files**:
- `apps/server/src/dipeo_server/api/middleware.py`
- `apps/server/src/dipeo_server/api/auth/` (new module)
- `apps/chatgpt-widgets/src/lib/graphql-client.ts`

### 2. GraphQL Persisted Queries
**Issue**: Accepting raw query strings is risky.

**Current**:
```typescript
export async function queryGraphQL<T>(
  query: string,
  variables?: Record<string, any>
)
```

**Recommended**:
```typescript
// Use query hashes for allowed operations
export async function queryGraphQL<T>(
  queryId: string,  // Hash of allowed query
  variables?: Record<string, any>
)
```

**Benefits**:
- Prevents arbitrary query injection
- Reduces payload size
- Enables query allowlisting

**Files**:
- `apps/chatgpt-widgets/src/lib/graphql-client.ts`
- Server-side persisted query registry

### 3. Rate Limiting
**Required**:
- Per-widget rate limits
- Per-user rate limits
- Backoff strategies

**Implementation**:
```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter

@app.post("/graphql")
@limiter.limit("100/minute")
async def graphql_endpoint(request: Request):
    # ...
```

**Files**:
- `apps/server/src/dipeo_server/api/middleware.py`
- `apps/server/requirements.txt` (add `slowapi`)

---

## Priority 5: Code Quality Improvements

### 1. Runtime Validation with Zod
**Issue**: Components accept props without runtime validation.

**Implementation**:
```typescript
import { z } from 'zod';

const ExecutionResultsPropsSchema = z.object({
  executionId: z.string().min(1),
});

function ExecutionResults() {
  const props = useWidgetProps<ExecutionResultsProps>();

  // Validate at runtime
  try {
    ExecutionResultsPropsSchema.parse(props);
  } catch (error) {
    return <WidgetLayout error={new Error('Invalid props')} />;
  }

  // ...
}
```

**Files**: All widget index files

### 2. Extract Magic Numbers
**Issue**: Hard-coded values scattered throughout code.

**Create Constants File**:
```typescript
// src/lib/constants.ts
export const WIDGET_STATE_POLL_INTERVAL = 100;
export const WIDGET_STATE_POLL_MAX_DELAY = 2000;
export const WIDGET_STATE_POLL_MAX_ATTEMPTS = 10;

export const EXECUTION_LIST_REFETCH_INTERVAL = 10000;
export const EXECUTION_RESULTS_REFETCH_INTERVAL = 5000;

export const SEARCH_DEBOUNCE_DELAY = 300;
```

**Files**:
- `src/lib/constants.ts` (new)
- All hook and component files

### 3. Consistent Error Handling
**Issue**: Inconsistent error message formatting and error object creation.

**Create Error Utilities**:
```typescript
// src/lib/errors.ts
export class WidgetError extends Error {
  constructor(
    message: string,
    public code: string,
    public details?: unknown
  ) {
    super(message);
    this.name = 'WidgetError';
  }
}

export function formatGraphQLError(error: unknown): Error {
  if (error instanceof Error) return error;
  if (typeof error === 'string') return new Error(error);
  return new Error('Unknown error occurred');
}
```

**Files**:
- `src/lib/errors.ts` (new)
- `src/hooks/use-graphql-query.ts`
- `src/lib/graphql-client.ts`

### 4. Improve Status Type Safety
**Issue**: Status types duplicated across files.

**Solution**: Export from generated GraphQL types (after implementing P1).

**Files**: All widget files

---

## Priority 6: Documentation Enhancements

### 1. Widget Usage Guide
**Issue**: README explains development but not ChatGPT app integration.

**Add Section**:
```markdown
## Using Widgets in ChatGPT Apps

### 1. Deploy DiPeO Server
Ensure your DiPeO server is accessible via HTTPS:
\`\`\`bash
make build-widgets
make dev-server
ngrok http 8000  # Or deploy to production
\`\`\`

### 2. Configure ChatGPT App
In your GPT configuration, add widget URLs:
- Execution Results: `https://your-server.com/widgets/execution-results-[hash].html`
- Execution List: `https://your-server.com/widgets/execution-list-[hash].html`
- Diagram List: `https://your-server.com/widgets/diagram-list-[hash].html`

### 3. Pass State from MCP Server
Your MCP tool responses should include widget metadata:
\`\`\`python
from dipeo_server.api.mcp_sdk_server.widgets import create_widget_response

return create_widget_response(
    widget_name="execution-results",
    data={"executionId": "exec_123"},
    text_summary="Execution completed successfully"
)
\`\`\`

### 4. Security Configuration
Set environment variables:
\`\`\`bash
export MCP_CHATGPT_ORIGINS="https://your-chatgpt-domain.com"
export WIDGET_API_KEY="your-secure-key"
\`\`\`
```

**Files**:
- `apps/chatgpt-widgets/README.md`
- `docs/features/chatgpt-apps-integration.md`

### 2. API Documentation
**Add**: GraphQL query documentation for widget developers.

**Create**:
```markdown
## Widget GraphQL API

### Execution Results Widget
\`\`\`graphql
query GetExecution($sessionId: String!) {
  execution(sessionId: $sessionId) {
    sessionId
    status
    diagramName
    startedAt
    completedAt
    metadata
  }
}
\`\`\`

### Execution List Widget
...
```

**Files**: `docs/features/widget-api-reference.md` (new)

### 3. Development Workflow
**Add**: Step-by-step guide for widget development.

**Topics**:
- Setting up development environment
- Creating new widgets
- Testing widgets locally
- Debugging widget state issues
- Building and deploying

**Files**: `apps/chatgpt-widgets/DEVELOPMENT.md` (new)

---

## Priority 7: Architecture Improvements

### 1. Shared Code with Main Frontend
**Issue**: Code duplication between `apps/web` and `apps/chatgpt-widgets`.

**Create Shared Package**:
```
apps/shared/
  src/
    graphql/
      client.ts          # Shared GraphQL client
      types.ts           # Common GraphQL types
    components/
      StatusBadge.tsx    # Shared UI components
      LoadingSpinner.tsx
    hooks/
      use-debounced-value.ts
      use-visibility.ts
    utils/
      errors.ts
      constants.ts
```

**Update Package Structure**:
```json
// packages.json workspace
{
  "workspaces": [
    "apps/*",
    "packages/*"
  ]
}
```

**Benefits**:
- Single source of truth
- Easier maintenance
- Consistent behavior across UIs

**Files**:
- Create `apps/shared/` package
- Update imports in both `apps/web` and `apps/chatgpt-widgets`
- Update `pnpm-workspace.yaml`

### 2. Widget Development Mode
**Add**: Hot-reload dev server for rapid widget development.

**Implementation**:
```typescript
// apps/chatgpt-widgets/dev-server.ts
import express from 'express';

const app = express();

// Mock widget state
app.get('/widget/:name', (req, res) => {
  res.send(`
    <script>
      window.oai = {
        widget: {
          setState: (state) => console.log('setState', state),
          getState: () => (${JSON.stringify(mockState)})
        }
      };
    </script>
    <script type="module" src="http://localhost:4445/src/${req.params.name}/index.tsx"></script>
  `);
});

app.listen(3001);
```

**Files**:
- `apps/chatgpt-widgets/dev-server.ts` (new)
- `apps/chatgpt-widgets/package.json` (add script)

---

## Priority 8: Monitoring & Analytics

### 1. Widget Performance Monitoring
**Add**:
- Widget load time tracking
- GraphQL query performance metrics
- Error rate monitoring

**Implementation**:
```typescript
// src/lib/analytics.ts
export function trackWidgetLoad(widgetName: string, loadTime: number) {
  // Send to analytics service
}

export function trackQueryPerformance(query: string, duration: number) {
  // Send to analytics service
}

export function trackError(error: Error, context: Record<string, any>) {
  // Send to error tracking service
}
```

**Files**:
- `src/lib/analytics.ts` (new)
- Integrate into all widgets

### 2. Usage Analytics
**Track**:
- Widget usage frequency
- Most viewed executions
- Search queries
- User interactions (button clicks, filters)

**Privacy Considerations**:
- Opt-in analytics
- No PII collection
- Aggregate data only

---

## Implementation Timeline

### Phase 1: Critical (Before Production)
1. GraphQL type generation (P1)
2. Basic test coverage (P2)
3. Authentication & authorization (P4.1)
4. Security documentation (P6)

**Estimated**: 1-2 weeks

### Phase 2: Essential (Before Scale)
1. Comprehensive test suite (P2)
2. Performance optimizations (P3)
3. Rate limiting (P4.3)
4. Error handling improvements (P5.3)

**Estimated**: 1-2 weeks

### Phase 3: Quality of Life
1. Runtime validation (P5.1)
2. Code cleanup (P5.2)
3. Enhanced documentation (P6)
4. Monitoring & analytics (P8)

**Estimated**: 1-2 weeks

### Phase 4: Advanced
1. Shared code architecture (P7.1)
2. Widget dev mode (P7.2)
3. WebSocket subscriptions (P3.3)
4. Persisted queries (P4.2)

**Estimated**: 2-3 weeks

---

## Success Criteria

### Code Quality
- [ ] 80%+ test coverage
- [ ] All TypeScript strict mode checks pass
- [ ] Zero linting errors
- [ ] All widgets use generated GraphQL types

### Performance
- [ ] Widget initial load < 1s
- [ ] GraphQL queries < 200ms p95
- [ ] Search debouncing implemented
- [ ] No unnecessary re-renders

### Security
- [ ] API authentication implemented
- [ ] Rate limiting active
- [ ] CORS properly configured
- [ ] Security audit passed

### Documentation
- [ ] Widget usage guide complete
- [ ] API documentation current
- [ ] Development workflow documented
- [ ] Troubleshooting guide available

---

## Notes

- This plan prioritizes production readiness over feature completeness
- Each priority can be implemented in separate PRs for easier review
- Security items (P4) should not be skipped or delayed
- Test coverage (P2) is essential for maintainability
- Consider user feedback after initial deployment for priority adjustments
