# DiPeO Frontend Development Guide

## 🎯 Overview

DiPeO is a visual programming environment for AI agent workflows, featuring:
- **Visual Diagram Editor**: React Flow-based canvas for creating agent workflows
- **Real-time Execution**: WebSocket monitoring of agent execution
- **Domain-Driven Design**: Separate TypeScript packages for domain models
- **Modern Stack**: React 18, TypeScript 5, Vite, Zustand, GraphQL

## 🚀 Quick Start

```bash
# Clone and setup
git clone https://github.com/sorryhyun/DiPeO.git
cd DiPeO
pnpm install

# Generate GraphQL types
./codegen.sh

# Start development
./run.sh          # Start frontend + backend
./dev.sh --frontend --watch  # Frontend only with hot reload
```

## 🏗️ Architecture

### Directory Structure
```
apps/web/src/
├── features/          # Feature-based modules
│   ├── diagram-editor/
│   ├── execution-monitor/
│   └── person-manager/
├── shared/           # Shared utilities and components
│   ├── components/
│   ├── hooks/
│   └── utils/
├── core/            # Core business logic
│   ├── store/       # Zustand stores
│   ├── types/       # TypeScript types
│   └── services/    # API services
└── pages/           # Route pages

packages/
├── domain-models/   # Domain entities and types
├── llm-yaml/       # LLM-friendly YAML format
└── ui-components/  # Reusable UI components
```

### Key Design Principles

1. **Feature-First Organization**: Group by feature, not file type
2. **Domain Separation**: Keep domain logic in packages
3. **Type Safety**: Leverage TypeScript's branded types and strict mode
4. **Composable Hooks**: Build complex functionality from simple hooks

## 💡 Core Patterns

### 1. Branded Types for Type Safety

```typescript
// Use branded types for domain IDs
export type NodeID = string & { __brand: 'NodeID' };
export type PersonID = string & { __brand: 'PersonID' };
export type ArrowID = string & { __brand: 'ArrowID' };

// Helper functions for type conversion
export const nodeId = (id: string): NodeID => id as NodeID;
export const personId = (id: string): PersonID => id as PersonID;
```

### 2. Unified Store Pattern

```typescript
// Combine related stores for better performance
export const useUnifiedStore = create<UnifiedState>()((set, get) => ({
  // Canvas state
  nodes: new Map(),
  arrows: new Map(),
  persons: new Map(),
  
  // UI state
  selectedId: null,
  selectedType: null,
  
  // Actions use immer for immutability
  addNode: (node) => set(produce(state => {
    state.nodes.set(node.id, node);
  })),
}));
```

### 3. Composable Hooks Architecture

```typescript
// Base hooks for single responsibilities
export const useCanvas = () => {
  const { zoom, position } = useUnifiedStore(
    useShallow(state => ({ zoom: state.zoom, position: state.position }))
  );
  return { zoom, position };
};

// Composite hooks for features
export const useDiagramEditor = () => {
  const canvas = useCanvas();
  const nodes = useNodes();
  const execution = useExecution();
  
  return { canvas, nodes, execution };
};
```

### 4. WebSocket Integration

```typescript
// Centralized WebSocket management
export const useExecutionMonitor = () => {
  const ws = useWebSocket('ws://localhost:8000/api/ws', {
    reconnectInterval: 3000,
    shouldReconnect: () => true,
  });

  useEffect(() => {
    if (ws.lastMessage) {
      const data = JSON.parse(ws.lastMessage.data);
      handleExecutionEvent(data);
    }
  }, [ws.lastMessage]);
};
```

## 🎨 Component Guidelines

### 1. Feature Components

```typescript
// features/diagram-editor/components/Canvas.tsx
export const DiagramCanvas: FC = () => {
  const { nodes, edges, onNodesChange } = useDiagramEditor();
  
  return (
    <ReactFlow
      nodes={nodes}
      edges={edges}
      onNodesChange={onNodesChange}
      nodeTypes={nodeTypes}
      fitView
    >
      <Background />
      <Controls />
      <MiniMap />
    </ReactFlow>
  );
};
```

### 2. Lazy Loading

```typescript
// Use React.lazy for heavy components
const LazyDiagramCanvas = lazy(() => import('./features/diagram-editor'));
const LazyExecutionView = lazy(() => import('./features/execution-monitor'));

// Wrap with Suspense
<Suspense fallback={<LoadingSpinner />}>
  <LazyDiagramCanvas />
</Suspense>
```

### 3. Memoization Strategy

```typescript
// Memoize expensive computations
export const useVisibleNodes = () => {
  const nodes = useNodes();
  const viewport = useViewport();
  
  return useMemo(() => 
    nodes.filter(node => isNodeInViewport(node, viewport)),
    [nodes, viewport]
  );
};
```

## ⚡ Performance Optimizations

### 1. Store Optimization

```typescript
// Use shallow comparison for better performance
const { selectedNodeId, selectedType } = useUnifiedStore(
  useShallow(state => ({
    selectedNodeId: state.selectedId,
    selectedType: state.selectedType
  }))
);

// Use Maps instead of arrays for O(1) lookups
nodes: Map<NodeID, DomainNode>
arrows: Map<ArrowID, DomainArrow>
```

### 2. React Flow Optimization

```typescript
// Optimize node rendering
const nodeTypes = useMemo(() => ({
  person: PersonNode,
  task: TaskNode,
  decision: DecisionNode,
}), []);

// Debounce viewport changes
const debouncedOnViewportChange = useDebouncedCallback(
  (viewport) => updateViewport(viewport),
  100
);
```

### 3. Bundle Optimization

```javascript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'react-flow': ['@xyflow/react'],
          'editor': ['./src/features/diagram-editor'],
          'execution': ['./src/features/execution-monitor'],
        }
      }
    }
  }
});
```

## 🧪 Testing Strategy

### 1. Unit Tests

```typescript
// Use Vitest for unit tests
describe('NodeOperations', () => {
  it('should add node with correct type', () => {
    const { result } = renderHook(() => useNodeOperations());
    
    act(() => {
      result.current.addNode('task', { x: 100, y: 100 });
    });
    
    expect(result.current.nodes.size).toBe(1);
  });
});
```

### 2. Integration Tests

```typescript
// Test complete features
describe('DiagramExecution', () => {
  it('should execute diagram via WebSocket', async () => {
    const { result } = renderHook(() => useExecution());
    
    await act(async () => {
      await result.current.executeDiagram(mockDiagram);
    });
    
    expect(result.current.status).toBe('completed');
  });
});
```

## 📦 Build & Deployment

### Production Build

```bash
# Build with optimizations
pnpm build:web

# Analyze bundle size
pnpm analyze
```

### Environment Configuration

```typescript
// src/config/environment.ts
export const config = {
  api: {
    baseUrl: import.meta.env.VITE_API_URL || 'http://localhost:8000',
    wsUrl: import.meta.env.VITE_WS_URL || 'ws://localhost:8000',
  },
  features: {
    enableWebSocket: import.meta.env.VITE_ENABLE_WS === 'true',
    debugMode: import.meta.env.DEV,
  }
};
```

## 🔧 Development Tools

### VS Code Extensions
- **ES7+ React snippets**: Quick component scaffolding
- **Prettier**: Code formatting
- **ESLint**: Code quality
- **TypeScript Error Lens**: Inline error display

### Chrome Extensions
- **React Developer Tools**: Component inspection
- **Redux DevTools**: State debugging (works with Zustand)

## 📋 Code Quality Checklist

### Before Committing
- [ ] TypeScript compiles without errors
- [ ] ESLint passes
- [ ] Unit tests pass
- [ ] No console.logs in production code
- [ ] Complex functions have JSDoc comments
- [ ] New features have corresponding tests

### Performance Checklist
- [ ] Heavy components are lazy loaded
- [ ] Lists use proper keys and virtualization
- [ ] Expensive computations are memoized
- [ ] Event handlers are debounced/throttled
- [ ] WebSocket connections are properly managed

## 🚦 Common Pitfalls & Solutions

### 1. Circular Dependencies
```typescript
// ❌ Avoid
import { NodeOperations } from '../node-operations';
import { ArrowOperations } from '../arrow-operations';

// ✅ Use dependency injection or events
export const useNodeOperations = (deps?: { onConnect?: () => void }) => {
  // ...
};
```

### 2. Over-fetching GraphQL
```typescript
// ✅ Use fragments for reusable selections
const NODE_FRAGMENT = gql`
  fragment NodeFields on Node {
    id
    type
    position
    data
  }
`;
```

### 3. Memory Leaks
```typescript
// ✅ Always cleanup subscriptions
useEffect(() => {
  const subscription = store.subscribe(handleChange);
  return () => subscription.unsubscribe();
}, []);
```

## 🎯 Future Improvements

1. **Module Federation**: Split features into micro-frontends
2. **Service Workers**: Offline diagram editing
3. **WebAssembly**: Performance-critical operations
4. **Incremental Migration**:
   - Adopt React Server Components for static content
   - Implement Suspense for data fetching

## 📚 Resources

- [Project Repository](https://github.com/sorryhyun/DiPeO)
- [React Flow Documentation](https://reactflow.dev)
- [Zustand Best Practices](https://github.com/pmndrs/zustand)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/)