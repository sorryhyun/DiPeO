# Backend to Frontend Migration Plan

## Overview

This plan outlines the migration of business logic from the Python backend (`apps/server`) to a TypeScript shared layer, while maintaining a thin backend for sensitive operations.

## Architecture Goals

1. **Thin Backend Layer**: Only handle sensitive operations (API keys, LLM calls, SSE streaming)
2. **Shared TypeScript Logic**: Business logic accessible to both frontend and backend
3. **Type-Safe Communication**: Use tRPC or similar for seamless API calls
4. **Security**: Keep API keys and sensitive data server-side only

## Migration Phases

  📁 File Structure Created

  apps/web/src/execution/
  ├── core/
  │   ├── execution-engine.ts          # Main orchestration engine
  │   ├── skip-manager.ts             # Existing
  │   └── loop-controller.ts          # Existing
  ├── executors/
  │   ├── base-executor.ts            # Abstract base classes
  │   ├── client-safe-executors.ts    # Browser-safe implementations
  │   ├── server-only-executors.ts    # Server-required implementations
  │   ├── client-executor-factory.ts  # Client factory
  │   ├── server-executor-factory.ts  # Server factory
  │   └── index.ts                    # Exports
  ├── execution-orchestrator.ts       # High-level execution interface
  └── index.ts                       # Main exports


### Phase 5: API Layer (tRPC)

**Purpose**: Create a type-safe API layer that seamlessly connects the TypeScript frontend with the thin backend. tRPC provides end-to-end type safety without code generation.

**Benefits**:
- No API contracts to maintain separately
- Automatic type inference from backend to frontend
- RPC-style calls feel like local function calls

```typescript
// server/trpc/routers/diagram.ts
export const diagramRouter = router({
  execute: protectedProcedure
    .input(z.object({ diagram: DiagramSchema }))
    .mutation(async ({ input, ctx }) => {
      // Thin wrapper around execution engine
      // Handles only LLM calls and sensitive ops
    }),
    
  validateApiKey: protectedProcedure
    .input(z.object({ provider: z.string(), key: z.string() }))
    .mutation(async ({ input }) => {
      // Server-side API key validation
    })
});
```

### Phase 6: Hybrid Execution Model

**Purpose**: Implement intelligent execution routing that runs nodes in the optimal environment. Client-safe nodes execute locally for speed, while sensitive operations are delegated to the server.

**Innovation**: This hybrid approach provides the best of both worlds - fast local execution when possible, secure server execution when necessary. The user experience remains seamless.

```typescript
// apps/web/src/features/diagram/hooks/useHybridExecution.ts
export function useHybridExecution() {
  const executeLocally = (nodes: Node[]) => {
    // Execute client-safe nodes locally
  };
  
  const executeRemotely = async (nodes: Node[]) => {
    // Execute server-only nodes via API
  };
  
  const executeHybrid = async (diagram: Diagram) => {
    // Smart routing based on node types
    const { clientNodes, serverNodes } = partitionNodes(diagram.nodes);
    
    // Execute in appropriate environment
    const clientResults = executeLocally(clientNodes);
    const serverResults = await executeRemotely(serverNodes);
    
    return mergeResults(clientResults, serverResults);
  };
}
```

## Implementation Strategy

## Components to Keep Server-Side

### Sensitive Operations
- **API Key Management**: Store, validate, encrypt
- **LLM API Calls**: OpenAI, Anthropic, Gemini, Grok
- **File System Access**: Server-side file operations
- **External APIs**: Notion, web search
- **Cost Tracking**: Usage and billing

### Streaming Infrastructure
- SSE/WebSocket connections
- Real-time execution updates
- Progress tracking

## Benefits

1. **Performance**: Client-side execution for non-LLM operations
2. **Type Safety**: Shared types between frontend and backend
3. **Maintainability**: Single source of truth for business logic
4. **Security**: API keys never exposed to client
5. **Flexibility**: Can execute entirely client-side for non-LLM diagrams

## Testing Strategy

1. **Unit Tests**: For all shared TypeScript modules
2. **Integration Tests**: For hybrid execution scenarios
3. **E2E Tests**: Full diagram execution flows
4. **Type Tests**: Ensure type consistency across boundaries

## Migration Checklist

- [ ] Create shared execution engine
- [ ] Implement client-safe executors
- [ ] Set up tRPC
- [ ] Create thin backend API
- [ ] Implement hybrid execution
- [ ] Update streaming for hybrid model
- [ ] Comprehensive testing
- [ ] Documentation update

* Note that execution typescript logic is currently being migrated to `apps/web/src/execution` and `apps/web/src/shared`.
* Shared types are declared in `types/shared.ts`