# DiPeO Frontend Hooks Architecture

## Overview

This directory contains the refactored hook system for the DiPeO frontend, implementing a factory-based pattern for creating reusable, type-safe React hooks. The architecture separates core utility hooks from domain-specific business logic hooks.

## Directory Structure

```
hooks/
├── core/           # Generic, reusable hook factories
│   ├── useResource.ts    # CRUD operations factory
│   ├── useStream.ts      # Real-time data streaming
│   ├── useForm.ts        # Form state management
│   └── index.ts
├── domain/         # Business-specific hooks using core factories
│   ├── useDiagram.ts     # Diagram operations
│   ├── useExecution.ts   # Execution monitoring
│   └── index.ts
└── README.md       # This documentation
```

## Core Hooks

### useResource

A generic factory for creating hooks that manage CRUD operations with consistent state management, error handling, and optimistic updates.

```typescript
import { useResource } from '@/hooks/core';

const { data, loading, error, fetch, create, update, delete } = useResource(
  'Product',
  {
    fetch: async (id) => api.getProduct(id),
    create: async (data) => api.createProduct(data),
    update: async (id, data) => api.updateProduct(id, data),
    delete: async (id) => api.deleteProduct(id),
    validate: async (data) => validateProduct(data)
  },
  {
    showToasts: true,
    optimisticUpdates: true,
    autoRefetch: true,
    refetchInterval: 60000
  }
);
```

**Features:**
- Automatic loading/error state management
- Optimistic updates with rollback on failure
- Built-in validation before create/update
- Auto-refetch with stale data detection
- Toast notifications for user feedback
- Caching and deduplication

### useStream

Factory for creating hooks that handle real-time data streams via GraphQL subscriptions, Server-Sent Events, or WebSockets.

```typescript
import { useStream } from '@/hooks/core';

const { data, buffer, connected, connect, disconnect, send } = useStream(
  'execution-updates',
  {
    protocol: 'sse',
    endpoint: '/api/execution/stream',
    bufferSize: 100,
    reconnect: true,
    reconnectDelay: 3000,
    onMessage: (data) => console.log('Received:', data),
    transform: (raw) => JSON.parse(raw)
  }
);
```

**Features:**
- Multiple protocol support (SSE, WebSocket, GraphQL)
- Automatic reconnection with exponential backoff
- Message buffering for history
- Connection state tracking
- Error recovery
- Type-safe message transformation

### useForm

Comprehensive form state management with validation, auto-save, and field-level error handling.

```typescript
import { useForm } from '@/hooks/core';
import { z } from 'zod';

const form = useForm({
  initialValues: { name: '', email: '' },
  validationSchema: z.object({
    name: z.string().min(2),
    email: z.string().email()
  }),
  validateOnChange: true,
  autoSave: true,
  autoSaveDelay: 1000,
  onSubmit: async (values) => {
    await api.saveUser(values);
  }
});

// In component
<input {...form.getFieldProps('name')} />
{form.errors.name && <span>{form.errors.name[0]}</span>}
```

**Features:**
- Zod schema validation
- Field-level and form-level validation
- Auto-save with debouncing
- Dirty/touched state tracking
- Error message management
- Submit state handling
- Field helpers for easy integration

## Domain Hooks

### useDiagram

Manages diagram operations using the useResource factory with store synchronization.

```typescript
import { useDiagram } from '@/hooks/domain';

const {
  diagram,
  loading,
  error,
  operations,
  addNode,
  updateNode,
  removeNode,
  clearDiagram
} = useDiagram({
  diagramId: 'diagram-123',
  autoLoad: true,
  syncWithStore: true,
  showToasts: true
});

// Load from file
await operations.loadFromFile(file);

// Export diagram
await operations.exportAs(DiagramFormat.YAML);

// Validate before save
const { isValid, errors } = operations.validate();
```

**Integration Points:**
- Unified store synchronization
- GraphQL mutations for persistence
- File import/export support
- Validation with error reporting
- Optimistic updates for better UX

### useExecution

Monitors diagram execution with real-time updates using the useStream factory.

```typescript
import { useExecution } from '@/hooks/domain';

const {
  execution,
  nodeStates,
  isRunning,
  progress,
  execute,
  abort,
  pauseNode,
  resumeNode
} = useExecution({
  protocol: 'sse',
  showToasts: true,
  debug: true
});

// Execute diagram
await execute(diagram, {
  variables: { input: 'data' },
  timeout: 300,
  maxIterations: 10
});

// Control execution
await pauseNode('node-123');
await abort();
```

**Features:**
- Real-time execution status updates
- Per-node state tracking
- Progress calculation
- Interactive control (pause/resume/skip)
- Debug logging
- Automatic reconnection

## Migration Guide

### From Old Pattern to New Pattern

**Before (scattered logic):**
```typescript
// Old pattern - logic mixed in component
function MyComponent() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  
  const fetchData = async () => {
    setLoading(true);
    try {
      const result = await api.getData();
      setData(result);
    } catch (err) {
      setError(err);
      toast.error('Failed to load');
    } finally {
      setLoading(false);
    }
  };
  
  // ... more boilerplate
}
```

**After (using factories):**
```typescript
// New pattern - clean separation
function MyComponent() {
  const resource = useResource('Data', {
    fetch: api.getData,
    update: api.updateData
  });
  
  // All state management handled by the hook
  if (resource.loading) return <Spinner />;
  if (resource.error) return <Error />;
  return <DataView data={resource.data} />;
}
```

### Step-by-Step Migration

1. **Identify the pattern** - CRUD, streaming, or form management
2. **Choose the appropriate factory** - useResource, useStream, or useForm
3. **Define operations** - Implement the required methods
4. **Configure options** - Set behavior preferences
5. **Replace old code** - Remove boilerplate, use hook returns
6. **Test thoroughly** - Ensure functionality is preserved

## Best Practices

### 1. Operation Definitions

Keep operations pure and focused:
```typescript
const operations = {
  // Good - single responsibility
  fetch: async (id) => api.getItem(id),
  
  // Bad - doing too much
  fetch: async (id) => {
    analytics.track('fetch');
    const data = await api.getItem(id);
    localStorage.setItem('lastFetch', Date.now());
    return transform(data);
  }
};
```

### 2. Error Handling

Let the factory handle common errors, only catch specific ones:
```typescript
const operations = {
  create: async (data) => {
    // Factory handles network errors, validation, etc.
    const result = await api.create(data);
    
    // Only handle business-specific errors
    if (result.requiresApproval) {
      throw new Error('Item requires approval before creation');
    }
    
    return result;
  }
};
```

### 3. Type Safety

Always provide proper types for better IDE support:
```typescript
interface Product {
  id: string;
  name: string;
  price: number;
}

const useProduct = (id: string) => {
  return useResource<Product>('Product', operations);
};
```

### 4. Composition

Combine multiple hooks for complex features:
```typescript
function useEditableDiagram() {
  const diagram = useDiagram();
  const execution = useExecution();
  const form = useForm({
    initialValues: diagram.diagram,
    onSubmit: async (values) => {
      await diagram.update(values);
      await execution.execute(values);
    }
  });
  
  return {
    ...diagram,
    ...execution,
    form
  };
}
```

## Performance Considerations

### Memoization

Operations should be memoized to prevent unnecessary re-renders:
```typescript
const operations = useMemo(() => ({
  fetch: async (id) => api.fetch(id),
  // ...
}), [api]); // Only recreate if api changes
```

### Debouncing

Use built-in debouncing for expensive operations:
```typescript
const form = useForm({
  autoSave: true,
  autoSaveDelay: 1000, // Debounce for 1 second
  onSubmit: expensiveSaveOperation
});
```

### Selective Updates

Use granular state updates to minimize re-renders:
```typescript
const { data, loading } = useResource('Data', operations, {
  // Only update what changed
  optimisticUpdates: true
});
```

## Testing

### Unit Testing Hooks

```typescript
import { renderHook, act } from '@testing-library/react-hooks';
import { useResource } from '@/hooks/core';

test('useResource fetches data', async () => {
  const mockFetch = jest.fn().mockResolvedValue({ id: 1, name: 'Test' });
  
  const { result, waitForNextUpdate } = renderHook(() =>
    useResource('Test', { fetch: mockFetch })
  );
  
  act(() => {
    result.current.fetch('1');
  });
  
  await waitForNextUpdate();
  
  expect(result.current.data).toEqual({ id: 1, name: 'Test' });
  expect(mockFetch).toHaveBeenCalledWith('1');
});
```

### Mocking in Components

```typescript
jest.mock('@/hooks/domain', () => ({
  useDiagram: () => ({
    diagram: mockDiagram,
    loading: false,
    error: null,
    operations: {
      validate: jest.fn().mockReturnValue({ isValid: true, errors: [] })
    }
  })
}));
```

## Troubleshooting

### Common Issues

1. **Infinite loops** - Ensure operations are memoized
2. **Stale closures** - Use callback refs for latest values
3. **Memory leaks** - Cleanup subscriptions in useEffect
4. **Race conditions** - Use abort controllers for fetch
5. **Type errors** - Explicitly type generic parameters

### Debug Mode

Enable debug logging for troubleshooting:
```typescript
const execution = useExecution({
  debug: true, // Logs all updates to console
  showToasts: true // Shows user-facing notifications
});
```

## Future Enhancements

- [ ] Add request caching and deduplication
- [ ] Implement optimistic UI patterns library
- [ ] Add hook composition utilities
- [ ] Create hook testing utilities
- [ ] Add performance monitoring
- [ ] Implement request queue management
- [ ] Add offline support with sync

## Contributing

When adding new hooks:
1. Determine if it should be core (generic) or domain (specific)
2. Use existing factories when possible
3. Follow the established patterns
4. Add comprehensive TypeScript types
5. Include usage examples in documentation
6. Write unit tests for new functionality
7. Update this README with new patterns