# AgentDiagram Web Frontend

Visual workflow editor for orchestrating multi-LLM agent systems with real-time execution and monitoring.

## 🚀 Quick Start

```bash
# Install dependencies
pnpm install

# Development server (http://localhost:3000)
pnpm dev

# Production build
pnpm build

# Preview production build
pnpm preview

# Bundle analysis
pnpm analyze
```

## 🛠️ Tech Stack

- **Framework**: React 19 + TypeScript 5
- **Build**: Vite 5 (with code splitting & tree shaking)
- **State**: Zustand 4 (with devtools & persistence)
- **Diagram**: React Flow 12 (node-based editor)
- **Styling**: Tailwind CSS 3 (with PostCSS)
- **Real-time**: Server-Sent Events (SSE)

## 📁 Architecture

```
src/
├── core/                 # Core state management
│   ├── contexts/        # React contexts (DiagramContext)
│   ├── hooks/           # Store selectors & state hooks
│   └── stores/          # Zustand stores (diagram, UI, execution, history)
├── engine/              # Execution engine & orchestration
│   ├── core/           # execution-engine.ts, loop-controller.ts, skip-manager.ts
│   ├── executors/      # Node execution logic
│   │   ├── client-safe/    # Start, Condition, Job, Endpoint
│   │   ├── server-only/    # PersonJob, PersonBatchJob, DB
│   │   └── *-factory.ts    # Environment-specific factories
│   ├── flow/           # dependency-resolver.ts, execution-planner.ts
│   └── execution-orchestrator.ts  # Main orchestration
├── features/            # Feature-based modules
│   ├── canvas/         # React Flow visual components
│   ├── conversation/   # Chat dashboard & history
│   ├── execution/      # Execution hooks & controls
│   ├── layout/         # TopBar, Sidebar, modals
│   ├── nodes/          # Node components & base classes
│   └── properties/     # Property panels & forms
├── serialization/       # Import/export (YAML, JSON)
├── shared/             # Cross-feature utilities
│   ├── components/     # Reusable UI components  
│   ├── types/          # TypeScript definitions
│   └── utils/          # Helper functions
└── declarations/        # Global type declarations
```

### Key Type Conventions

- **Strict TypeScript**: `noImplicitAny`, `strictNullChecks`, `noUncheckedIndexedAccess`
- **Discriminated Unions**: `DiagramNodeData` with `type` discriminator
- **Interface Inheritance**: `BaseBlockData` extended by specific node types
- **Enum vs Union Types**: Mix of both (`NodeType` union, `LLMService` enum)
- **Error Hierarchy**: Custom error classes extending `AgentDiagramException`

### Key Stores

- **`consolidatedDiagramStore`** - Nodes, arrows, persons, API keys
- **`consolidatedUIStore`** - UI state, selections, dashboard tabs  
- **`executionStore`** - Runtime state, running nodes
- **`historyStore`** - Undo/redo with Immer patches

## 🔧 Development Guide

### Adding a New Node Type

1. **Define the node config** in `shared/types/nodeConfig.ts`:
```typescript
export const UNIFIED_NODE_CONFIGS = {
  my_node: {
    emoji: '🎯',
    label: 'My Node',
    reactFlowType: 'myNode',
    handles: [...],
    propertyFields: [...]
  }
}
```

2. **Create the node component** in `features/nodes/components/nodes/MyNode.tsx`:
```typescript
const MyNode: React.FC<NodeProps> = ({ id, data, selected }) => {
  return (
    <GenericNode id={id} data={data} selected={selected} nodeType="myNode">
      {/* Node content */}
    </GenericNode>
  );
};
```

3. **Add to lazy exports** in `features/nodes/components/nodes/index.ts`

### Execution System

The execution system is environment-aware with separate executors for client/server:

```typescript
// Client-safe executors (execution/executors/client-safe/)
StartExecutor, ConditionExecutor, JobExecutor, EndpointExecutor

// Server-only executors (execution/executors/server-only/)  
PersonJobExecutor, PersonBatchJobExecutor, DBExecutor

// Auto-detect environment and create appropriate factory
import { createExecutorFactory } from '@/execution/executors';
const factory = createExecutorFactory(); // 'client' | 'server'
const executor = factory.createExecutor('person_job');
```

**Adding New Executors:**
1. Extend `ClientSafeExecutor` or `ServerOnlyExecutor` 
2. Implement `validateInputs()` and `execute()` methods
3. Add to appropriate factory in `registerExecutors()`
4. Export from directory index file

### Working with Stores

```typescript
// Component usage (optimized selectors)
import { useNodes, useSelectedElement } from '@/shared/hooks/useStoreSelectors';

const MyComponent = () => {
  const { nodes, addNode } = useNodes();
  const { selectedNodeId, setSelectedNodeId } = useSelectedElement();
  
  // Direct store access (when needed)
  const store = useConsolidatedDiagramStore.getState();
};
```

### Real-time Execution

The diagram runner uses SSE for streaming execution updates:

```typescript
import { useDiagramRunner } from '@/features/diagram/hooks/useDiagramRunner';

const { runStatus, handleRunDiagram, stopExecution } = useDiagramRunner();
```

### Property Panels

Property panels use a configuration-driven system:

```typescript
// features/properties/configs/myNodeConfig.ts
export const myNodeConfig: PanelConfig<MyNodeData> = {
  layout: 'twoColumn',
  leftColumn: [
    { type: 'text', name: 'label', label: 'Label' }
  ],
  rightColumn: [
    { type: 'textarea', name: 'prompt', label: 'Prompt' }
  ]
};
```

## 🎯 Key Concepts

### Node System
- **Unified Config**: Single source of truth for node types
- **Base Components**: Located in `features/nodes/components/base/`
  - `BaseNode` → `GenericNode` → Specific nodes
- **Auto Handles**: Handle positions derived from config
- **Flippable**: Nodes can flip handle positions

### Execution Flow
1. Export diagram → Sanitize → Send to backend
2. SSE stream updates → Update execution store
3. Visual feedback → Running nodes pulse/glow
4. Conversation updates → Real-time message streaming

### Memory Layer
- 3D tilted view showing underground memory storage
- Toggle with button or `isMemoryLayerTilted` state
- Connected to PersonJob nodes

## 🔨 Common Tasks

### Import/Export
```typescript
// YAML export
const { handleExportYAML } = useDiagramActions();

// JSON save to backend
const { handleSaveToDirectory } = useDiagramActions();
```

### API Key Management
```typescript
// Load from backend
const { loadApiKeys } = useConsolidatedDiagramStore();
await loadApiKeys();

// Add new key
const res = await fetch('/api/api-keys', {
  method: 'POST',
  body: JSON.stringify({ name, service, key })
});
```

### Conversation Monitoring
```typescript
// Enable polling for real-time updates
const { conversationData, fetchConversationData } = useConversationData(filters);

// Export conversations
downloadJson(conversationData, 'conversation.json');
```

## ⚙️ Configuration

### Environment Variables
```env
# Backend API host (default: localhost:8000)
VITE_API_HOST=localhost:8000
```

### Build Optimization
- Code splitting by feature
- Lazy loading for heavy components
- Tree shaking for unused code
- CSS purging for Tailwind

### Proxy Configuration
Dev server proxies `/api/*` requests to backend:
```typescript
// vite.config.ts
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true
  }
}
```

## 🐛 Troubleshooting

### Common Issues

**Nodes not updating visually**
- Check `useNodeExecutionState` hook is used
- Verify `data-node-running` attribute in BaseNode
- Ensure execution store updates are propagating

**API key errors**
- Backend must return keys in correct format
- Frontend stores only `keyReference`, not actual keys
- Check `/api/api-keys` endpoint is accessible

**SSE connection drops**
- Auto-reconnect is built-in (5s delay)
- Check backend CORS headers
- Verify proxy configuration

**Bundle size warnings**
- Run `pnpm analyze` to identify large chunks
- Consider dynamic imports for features
- Check for duplicate dependencies

**Executor environment errors**
- Client-safe: Start, Condition, Job, Endpoint nodes
- Server-only: PersonJob, PersonBatchJob, DB nodes require backend
- Use `createExecutorFactory()` for environment detection
- Check `getExecutionCapabilities()` for supported operations

### Performance Tips

1. **Use memoized selectors** to prevent re-renders
2. **Lazy load** heavy components (modals, panels)
3. **Virtualize** long lists (conversations)
4. **Debounce** property updates
5. **Profile** with React DevTools

## 📚 Key Hooks

- `useDiagramRunner()` - Execute workflows with SSE
- `useHybridExecution()` - Client/server execution coordination  
- `usePropertyPanel()` - Form state for property panels
- `useNodeExecutionState(id)` - Node-specific execution state
- `useCanvasState()` - Optimized canvas operations
- `useHistoryActions()` - Undo/redo functionality
- `useExecutionMonitor()` - Real-time execution status tracking

## 🔗 Links

- [Backend API Docs](http://localhost:8000/docs)
- [React Flow Docs](https://reactflow.dev/)
- [Zustand Docs](https://docs.pmnd.rs/zustand)
- [Tailwind Docs](https://tailwindcss.com/)