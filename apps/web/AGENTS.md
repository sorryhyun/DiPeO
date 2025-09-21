# Web Frontend

React-based visual diagram editor for DiPeO.

## Tech Stack
- React 19 + TypeScript + Vite
- XYFlow (diagram editing)
- Apollo Client (GraphQL)
- Zustand (state management)
- TailwindCSS + React Hook Form + Zod

## Commands
```bash
pnpm dev                # Start dev server (localhost:3000)
pnpm build              # Production build
pnpm typecheck          # TypeScript checking
pnpm codegen            # Generate GraphQL types
pnpm lint:fix           # Auto-fix linting
```

## Architecture
```
/apps/web/src/
├── __generated__/      # Generated GraphQL types (DO NOT EDIT)
├── domain/             # Business logic by domain
│   ├── diagram/        # Diagram editing, properties, personas
│   └── execution/      # Execution monitoring, conversations
├── infrastructure/     # Technical services
│   ├── store/          # Zustand state management
│   └── hooks/          # Cross-cutting hooks
├── lib/graphql/        # GraphQL client
└── ui/                 # Presentation layer
    └── components/     # UI components
```

### Key Imports
```typescript
// Domain hooks & services
import { useDiagramManager } from '@/domain/diagram';
import { useExecution } from '@/domain/execution';
import { useStore } from '@/infrastructure/store';

// Generated GraphQL
import { useGetDiagramQuery } from '@/__generated__/graphql';
```

## Key Concepts

### State Management (Zustand)
- Flattened store with slices: `diagram`, `execution`, `person`, `ui`
- Access via hooks: `useStore()`
- Factory patterns for CRUD operations

### GraphQL
- Queries in `/lib/graphql/queries/`
- Generated hooks in `/__generated__/`
- Real-time subscriptions for updates

### Node System
- Configs generated from TypeScript specs
- Components in `/ui/components/diagram/nodes/`
- Base classes: `BaseNode`, `ConfigurableNode`

### Forms
- React Hook Form + Zod validation
- Auto-save with debouncing
- Dynamic field rendering

## Development Patterns

### Components
```typescript
// Named exports via index.ts
export { MyComponent } from './MyComponent';

// Composition over inheritance
const EnhancedNode = withRightClickDrag(BaseNode);
```

### State & GraphQL
```typescript
// Zustand updates
set((state) => { state.nodes[nodeId] = data; });

// GraphQL hooks
const { data, loading } = useGetDiagramQuery({ 
  variables: { id },
  skip: !id 
});
```

### Styling
- TailwindCSS utilities
- Dark mode via CSS variables


## Infrastructure Services

| Service | Purpose | Location |
|---------|---------|----------|
| ConversionService | Type conversions, GraphQL transforms | `/infrastructure/converters/` |
| NodeService | Node specs, field configs | `/infrastructure/services/` |
| ValidationService | Zod validation, error messages | `/infrastructure/services/` |


## Common Patterns

```typescript
// Custom hooks
function useDiagramManager() {
  const store = useStore();
  return { diagram: store.diagram, save: () => {} };
}

// Factory functions
const createNodeConfig = (spec: NodeSpec): NodeConfig => ({ 
  type: spec.type, 
  fields: generateFields(spec) 
});

// Error boundaries
<ErrorBoundary fallback={<ErrorFallback />}>
  <DiagramEditor />
</ErrorBoundary>
```

## Important Notes

- **Never edit generated files** - Modify TypeScript specs and run codegen
- **Use pnpm** for package management
- **Maintain type safety** - avoid `any` types
- **Extract complex logic** to hooks

## URL Parameters

- `?diagram={format}/{filename}` - Load diagram
- `?monitor=true` - Monitor mode
- `?debug=true` - Debug mode
