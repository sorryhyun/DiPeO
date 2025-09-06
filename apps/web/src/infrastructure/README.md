# DiPeO Frontend Infrastructure Layer

## Overview

The `apps/web/src/infrastructure` directory contains **technical infrastructure and cross-cutting concerns** that support the domain and UI layers. This layer handles state management, API communication, data conversion, caching, and other technical services that enable the business logic to function without dealing with implementation details.

## Architecture

### Infrastructure Role

```
┌─────────────────────────────────────┐
│         UI Layer                    │
│     (Presentation)                  │
└────────────┬────────────────────────┘
             │
    ┌────────▼────────────┐
    │   Domain Layer      │
    │  (Business Logic)   │
    └────────┬────────────┘
             │ Uses
    ┌────────▼────────────────┐
    │  Infrastructure Layer   │ ◄── Technical Services
    │   (This Directory)      │
    ├─────────────────────────┤
    │ • State Management      │
    │ • API Communication     │
    │ • Data Conversion       │
    │ • Caching & Storage     │
    │ • Cross-cutting Hooks   │
    └─────────────────────────┘
```

### Directory Structure

```
infrastructure/
├── store/              # Zustand state management
│   ├── unifiedStore.ts # Main store instance
│   ├── slices/         # Store slices by domain
│   ├── selectors/      # Memoized selectors
│   ├── middleware/     # Store middleware
│   └── helpers/        # Store utilities
├── api/                # API setup & configuration
│   └── graphql.ts      # Apollo Client setup
├── converters/         # Data transformation services
│   ├── node-converter.ts
│   ├── diagram-converter.ts
│   └── ConversionService.ts
├── services/           # Technical services
│   ├── validation-service.ts
│   ├── node-service.ts
│   └── diagram-operations.ts
├── hooks/              # Cross-cutting React hooks
│   ├── core/           # Core hook patterns
│   ├── forms/          # Form management
│   └── factories/      # Hook factories
├── providers/          # React context providers
│   └── ThemeContext.tsx
├── types/              # Shared type definitions
│   ├── branded.ts      # Branded types
│   ├── guards.ts       # Type guards
│   └── utilities.ts    # Utility types
└── utils/              # Infrastructure utilities
```

## Core Components

### 1. State Management (`/store/`)

Centralized state using Zustand with slices pattern:

#### Unified Store (`unifiedStore.ts`)

```typescript
// Main store combining all slices
export const useUnifiedStore = create<UnifiedStore>()(
  devtools(
    immer((...args) => ({
      // Compose slices
      ...createDiagramSlice(...args),
      ...createExecutionSlice(...args),
      ...createPersonSlice(...args),
      ...createUISlice(...args),
      ...createComputedSlice(...args),
      
      // Global actions
      reset: () => set(initialState),
      hydrate: (state) => set(state),
    }))
  )
);
```

#### Store Slices (`slices/`)

**Diagram Slice** (`diagram.ts`):
```typescript
export interface DiagramSlice {
  // State
  nodes: Record<NodeID, NodeData>;
  edges: Record<EdgeID, EdgeData>;
  viewport: Viewport;
  selectedNodeIds: Set<NodeID>;
  selectedEdgeIds: Set<EdgeID>;
  
  // Actions
  addNode: (node: NodeData) => void;
  updateNode: (id: NodeID, updates: Partial<NodeData>) => void;
  deleteNode: (id: NodeID) => void;
  
  addEdge: (edge: EdgeData) => void;
  updateEdge: (id: EdgeID, updates: Partial<EdgeData>) => void;
  deleteEdge: (id: EdgeID) => void;
  
  selectNodes: (ids: NodeID[]) => void;
  clearSelection: () => void;
  
  // Bulk operations
  importDiagram: (diagram: DomainDiagram) => void;
  clearDiagram: () => void;
}
```

**Execution Slice** (`execution.ts`):
```typescript
export interface ExecutionSlice {
  // State
  currentExecutionId: string | null;
  executionState: ExecutionState | null;
  nodeStates: Record<NodeID, NodeExecutionState>;
  executionHistory: ExecutionRecord[];
  
  // Actions
  startExecution: (executionId: string) => void;
  updateNodeState: (nodeId: NodeID, state: NodeExecutionState) => void;
  completeExecution: (result: ExecutionResult) => void;
  abortExecution: () => void;
  
  // Real-time updates
  handleExecutionUpdate: (update: ExecutionUpdate) => void;
  
  // History
  addToHistory: (record: ExecutionRecord) => void;
  clearHistory: () => void;
}
```

**Person Slice** (`person.ts`):
```typescript
export interface PersonSlice {
  // State
  persons: Record<PersonID, Person>;
  activePersonId: PersonID | null;
  conversations: Record<PersonID, Conversation>;
  
  // Actions
  addPerson: (person: Person) => void;
  updatePerson: (id: PersonID, updates: Partial<Person>) => void;
  deletePerson: (id: PersonID) => void;
  setActivePerson: (id: PersonID) => void;
  
  // Conversation management
  addMessage: (personId: PersonID, message: Message) => void;
  clearConversation: (personId: PersonID) => void;
}
```

#### Store Helpers (`helpers/`)

**CRUD Factory** (`crudFactory.ts`):
```typescript
// Generate CRUD operations for entities
export function createCRUDSlice<T extends { id: string }>(
  name: string,
  initialState: Record<string, T> = {}
) {
  return (set: SetState) => ({
    [`${name}s`]: initialState,
    
    [`add${capitalize(name)}`]: (item: T) =>
      set((state) => {
        state[`${name}s`][item.id] = item;
      }),
    
    [`update${capitalize(name)}`]: (id: string, updates: Partial<T>) =>
      set((state) => {
        if (state[`${name}s`][id]) {
          Object.assign(state[`${name}s`][id], updates);
        }
      }),
    
    [`delete${capitalize(name)}`]: (id: string) =>
      set((state) => {
        delete state[`${name}s`][id];
      }),
  });
}
```

**Computed Getters** (`computedGetters.ts`):
```typescript
// Memoized computed values
export const computedGetters = {
  getNodeById: (state: UnifiedStore) => (id: NodeID) => 
    state.nodes[id],
  
  getSelectedNodes: (state: UnifiedStore) =>
    Array.from(state.selectedNodeIds).map(id => state.nodes[id]),
  
  getNodesByType: (state: UnifiedStore) => (type: NodeType) =>
    Object.values(state.nodes).filter(node => node.type === type),
  
  getExecutionProgress: (state: UnifiedStore) => {
    const total = Object.keys(state.nodes).length;
    const completed = Object.values(state.nodeStates)
      .filter(s => s.status === 'completed').length;
    return total > 0 ? (completed / total) * 100 : 0;
  }
};
```

#### Store Middleware (`middleware/`)

```typescript
// Side effects middleware
export const sideEffectsMiddleware = (config: StateCreator) => 
  (set: SetState, get: GetState, api: StoreApi) => {
    const setState = (updater: any) => {
      const prevState = get();
      set(updater);
      const nextState = get();
      
      // Trigger side effects
      if (prevState.selectedNodeIds !== nextState.selectedNodeIds) {
        // Update properties panel
        emitSelectionChange(nextState.selectedNodeIds);
      }
      
      if (prevState.nodes !== nextState.nodes) {
        // Mark diagram as dirty
        set({ isDirty: true });
      }
    };
    
    return config(setState, get, api);
  };
```

### 2. API Layer (`/api/`)

GraphQL client configuration:

```typescript
// Apollo Client setup
const httpLink = createHttpLink({
  uri: 'http://localhost:8000/graphql',
});

const wsLink = new GraphQLWsLink(
  createClient({
    url: 'ws://localhost:8000/graphql',
    reconnect: true,
    connectionParams: {
      authToken: getAuthToken(),
    },
  })
);

// Split links based on operation type
const splitLink = split(
  ({ query }) => {
    const definition = getMainDefinition(query);
    return (
      definition.kind === 'OperationDefinition' &&
      definition.operation === 'subscription'
    );
  },
  wsLink,
  httpLink
);

export const apolloClient = new ApolloClient({
  link: splitLink,
  cache: new InMemoryCache({
    typePolicies: {
      // Custom cache policies
      Diagram: {
        keyFields: ['id'],
        merge: true,
      },
      Execution: {
        keyFields: ['id'],
        fields: {
          nodeStates: {
            merge: false, // Replace array
          },
        },
      },
    },
  }),
});
```

### 3. Conversion Services (`/converters/`)

Data transformation between layers:

#### ConversionService (`ConversionService.ts`)

```typescript
export class ConversionService {
  // Node conversions
  static domainNodeToGraphQL(node: DomainNode): GraphQLNode {
    return {
      id: node.id,
      type: this.nodeTypeToString(node.type),
      position: { x: node.x, y: node.y },
      data: this.serializeNodeData(node.data),
    };
  }
  
  static graphQLNodeToDomain(node: GraphQLNode): DomainNode {
    return {
      id: node.id,
      type: this.stringToNodeType(node.type),
      x: node.position.x,
      y: node.position.y,
      data: this.deserializeNodeData(node.data),
    };
  }
  
  // Handle conversions
  static createHandleId(nodeId: string, handleType: 'source' | 'target', index: number): string {
    return `${nodeId}-${handleType}-${index}`;
  }
  
  static parseHandleId(handleId: string): HandleInfo {
    const [nodeId, type, index] = handleId.split('-');
    return {
      nodeId,
      type: type as 'source' | 'target',
      index: parseInt(index, 10),
    };
  }
  
  // Diagram conversions
  static domainDiagramToExecutable(diagram: DomainDiagram): ExecutableDiagram {
    return {
      nodes: Object.values(diagram.nodes).map(this.domainNodeToExecutable),
      edges: Object.values(diagram.edges).map(this.domainEdgeToExecutable),
      metadata: diagram.metadata,
    };
  }
}
```

### 4. Technical Services (`/services/`)

#### Validation Service (`validation-service.ts`)

```typescript
export class ValidationService {
  private static validators = new Map<string, ZodSchema>();
  
  // Register validators for node types
  static registerValidator(nodeType: string, schema: ZodSchema) {
    this.validators.set(nodeType, schema);
  }
  
  // Validate node data
  static validateNodeData(nodeType: string, data: any): ValidationResult {
    const schema = this.validators.get(nodeType);
    if (!schema) {
      return { isValid: true };
    }
    
    try {
      schema.parse(data);
      return { isValid: true };
    } catch (error) {
      if (error instanceof ZodError) {
        return {
          isValid: false,
          errors: error.errors.map(e => ({
            field: e.path.join('.'),
            message: e.message,
          })),
        };
      }
      throw error;
    }
  }
  
  // Field-level validation
  static validateField(nodeType: string, field: string, value: any): string | null {
    const schema = this.validators.get(nodeType);
    if (!schema) return null;
    
    try {
      // Validate single field
      const fieldSchema = schema.shape[field];
      fieldSchema?.parse(value);
      return null;
    } catch (error) {
      return error.message;
    }
  }
}
```

#### Node Service (`node-service.ts`)

```typescript
export class NodeService {
  private static nodeSpecs = new Map<string, NodeSpec>();
  private static nodeCategories = new Map<string, NodeSpec[]>();
  
  // Get node specification
  static getNodeSpec(nodeType: string): NodeSpec | undefined {
    return this.nodeSpecs.get(nodeType);
  }
  
  // Get nodes by category
  static getNodesByCategory(category: string): NodeSpec[] {
    return this.nodeCategories.get(category) || [];
  }
  
  // Get field configuration
  static getFieldConfig(nodeType: string, fieldName: string): FieldConfig | undefined {
    const spec = this.getNodeSpec(nodeType);
    return spec?.fields.find(f => f.name === fieldName);
  }
  
  // Generate default values
  static getDefaultValues(nodeType: string): Record<string, any> {
    const spec = this.getNodeSpec(nodeType);
    if (!spec) return {};
    
    return spec.fields.reduce((acc, field) => {
      if (field.defaultValue !== undefined) {
        acc[field.name] = field.defaultValue;
      }
      return acc;
    }, {} as Record<string, any>);
  }
}
```

### 5. Infrastructure Hooks (`/hooks/`)

#### Core Hooks (`core/`)

**useResource** (`useResource.ts`):
```typescript
// Generic resource loading hook
export function useResource<T>(
  loader: () => Promise<T>,
  deps: DependencyList = []
): ResourceState<T> {
  const [state, setState] = useState<ResourceState<T>>({
    data: null,
    loading: true,
    error: null,
  });
  
  useEffect(() => {
    let cancelled = false;
    
    setState(prev => ({ ...prev, loading: true }));
    
    loader()
      .then(data => {
        if (!cancelled) {
          setState({ data, loading: false, error: null });
        }
      })
      .catch(error => {
        if (!cancelled) {
          setState({ data: null, loading: false, error });
        }
      });
    
    return () => {
      cancelled = true;
    };
  }, deps);
  
  return state;
}
```

**useStream** (`useStream.ts`):
```typescript
// Server-sent events streaming
export function useStream<T>(url: string): StreamState<T> {
  const [data, setData] = useState<T[]>([]);
  const [connected, setConnected] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  
  useEffect(() => {
    const eventSource = new EventSource(url);
    
    eventSource.onopen = () => setConnected(true);
    eventSource.onerror = (e) => {
      setConnected(false);
      setError(new Error('Connection failed'));
    };
    
    eventSource.onmessage = (event) => {
      try {
        const item = JSON.parse(event.data) as T;
        setData(prev => [...prev, item]);
      } catch (e) {
        setError(new Error('Parse error'));
      }
    };
    
    return () => eventSource.close();
  }, [url]);
  
  return { data, connected, error };
}
```

#### Form Hooks (`forms/`)

**useFormManager** (`useFormManager.ts`):
```typescript
export function useFormManager<T extends Record<string, any>>(
  initialValues: T,
  validationSchema?: ZodSchema
) {
  const [values, setValues] = useState(initialValues);
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [touched, setTouched] = useState<Record<string, boolean>>({});
  const [isDirty, setIsDirty] = useState(false);
  
  const validateField = useCallback((name: string, value: any) => {
    if (!validationSchema) return null;
    
    try {
      const fieldSchema = validationSchema.shape[name];
      fieldSchema?.parse(value);
      return null;
    } catch (error) {
      return error.message;
    }
  }, [validationSchema]);
  
  const handleChange = useCallback((name: string, value: any) => {
    setValues(prev => ({ ...prev, [name]: value }));
    setIsDirty(true);
    
    const error = validateField(name, value);
    setErrors(prev => ({
      ...prev,
      [name]: error || undefined,
    }));
  }, [validateField]);
  
  const handleBlur = useCallback((name: string) => {
    setTouched(prev => ({ ...prev, [name]: true }));
  }, []);
  
  const handleSubmit = useCallback(async (onSubmit: (values: T) => Promise<void>) => {
    // Validate all fields
    const allErrors: Record<string, string> = {};
    
    for (const [key, value] of Object.entries(values)) {
      const error = validateField(key, value);
      if (error) {
        allErrors[key] = error;
      }
    }
    
    if (Object.keys(allErrors).length > 0) {
      setErrors(allErrors);
      setTouched(Object.keys(values).reduce((acc, key) => {
        acc[key] = true;
        return acc;
      }, {} as Record<string, boolean>));
      return;
    }
    
    await onSubmit(values);
    setIsDirty(false);
  }, [values, validateField]);
  
  return {
    values,
    errors,
    touched,
    isDirty,
    handleChange,
    handleBlur,
    handleSubmit,
    reset: () => {
      setValues(initialValues);
      setErrors({});
      setTouched({});
      setIsDirty(false);
    },
  };
}
```

**useFormAutoSave** (`useFormAutoSave.ts`):
```typescript
export function useFormAutoSave<T>(
  values: T,
  save: (values: T) => Promise<void>,
  options: AutoSaveOptions = {}
) {
  const {
    delay = 1000,
    enabled = true,
    onSave,
    onError,
  } = options;
  
  const [saving, setSaving] = useState(false);
  const [lastSaved, setLastSaved] = useState<Date | null>(null);
  
  const debouncedSave = useMemo(
    () => debounce(async (data: T) => {
      if (!enabled) return;
      
      setSaving(true);
      try {
        await save(data);
        setLastSaved(new Date());
        onSave?.();
      } catch (error) {
        onError?.(error);
      } finally {
        setSaving(false);
      }
    }, delay),
    [save, delay, enabled, onSave, onError]
  );
  
  useEffect(() => {
    debouncedSave(values);
  }, [values, debouncedSave]);
  
  return {
    saving,
    lastSaved,
    forceSave: () => debouncedSave.flush(),
  };
}
```

### 6. Type System (`/types/`)

#### Branded Types (`branded.ts`)

```typescript
// Type-safe IDs using branding
export type Brand<T, B> = T & { __brand: B };

export type NodeID = Brand<string, 'NodeID'>;
export type EdgeID = Brand<string, 'EdgeID'>;
export type PersonID = Brand<string, 'PersonID'>;
export type ExecutionID = Brand<string, 'ExecutionID'>;

// Constructor functions
export const NodeID = (id: string): NodeID => id as NodeID;
export const EdgeID = (id: string): EdgeID => id as EdgeID;
export const PersonID = (id: string): PersonID => id as PersonID;
export const ExecutionID = (id: string): ExecutionID => id as ExecutionID;

// Type guards
export const isNodeID = (id: string): id is NodeID => 
  id.startsWith('node_');
export const isEdgeID = (id: string): id is EdgeID => 
  id.startsWith('edge_');
```

#### Type Guards (`guards.ts`)

```typescript
// Runtime type checking
export function isNode(obj: any): obj is Node {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    typeof obj.id === 'string' &&
    typeof obj.type === 'string' &&
    typeof obj.position === 'object'
  );
}

export function isEdge(obj: any): obj is Edge {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    typeof obj.id === 'string' &&
    typeof obj.source === 'string' &&
    typeof obj.target === 'string'
  );
}

export function isDiagram(obj: any): obj is Diagram {
  return (
    typeof obj === 'object' &&
    obj !== null &&
    Array.isArray(obj.nodes) &&
    Array.isArray(obj.edges) &&
    obj.nodes.every(isNode) &&
    obj.edges.every(isEdge)
  );
}
```

## Key Patterns

### 1. Store Factory Pattern

```typescript
// Create store slices using factories
const createEntitySlice = (name: string) => (set) => ({
  [`${name}s`]: {},
  [`add${name}`]: (item) => set(state => {
    state[`${name}s`][item.id] = item;
  }),
  [`update${name}`]: (id, updates) => set(state => {
    Object.assign(state[`${name}s`][id], updates);
  }),
  [`delete${name}`]: (id) => set(state => {
    delete state[`${name}s`][id];
  }),
});
```

### 2. Service Locator Pattern

```typescript
// Central service registry
class ServiceRegistry {
  private static services = new Map<string, any>();
  
  static register<T>(key: string, service: T): void {
    this.services.set(key, service);
  }
  
  static get<T>(key: string): T {
    const service = this.services.get(key);
    if (!service) {
      throw new Error(`Service ${key} not found`);
    }
    return service;
  }
}

// Register services
ServiceRegistry.register('validation', new ValidationService());
ServiceRegistry.register('conversion', new ConversionService());
```

### 3. Hook Composition

```typescript
// Compose multiple hooks
export function useComposedHook() {
  const store = useUnifiedStore();
  const validation = useValidation();
  const autosave = useAutoSave();
  
  return {
    ...store,
    validate: validation.validate,
    save: autosave.save,
  };
}
```

### 4. Memoized Selectors

```typescript
// Create memoized selectors
const selectNodesByType = createSelector(
  [(state: UnifiedStore) => state.nodes, (_: any, type: string) => type],
  (nodes, type) => Object.values(nodes).filter(n => n.type === type)
);

// Use in components
function Component() {
  const personNodes = useUnifiedStore(state => 
    selectNodesByType(state, 'person')
  );
}
```

## Testing Strategy

### Unit Tests

```typescript
describe('ConversionService', () => {
  it('should convert domain node to GraphQL', () => {
    const domainNode = {
      id: 'node1',
      type: NodeType.PersonJob,
      x: 100,
      y: 200,
      data: { prompt: 'test' },
    };
    
    const graphqlNode = ConversionService.domainNodeToGraphQL(domainNode);
    
    expect(graphqlNode).toEqual({
      id: 'node1',
      type: 'person_job',
      position: { x: 100, y: 200 },
      data: { prompt: 'test' },
    });
  });
});
```

### Integration Tests

```typescript
describe('UnifiedStore', () => {
  it('should update node and mark diagram as dirty', () => {
    const { result } = renderHook(() => useUnifiedStore());
    
    act(() => {
      result.current.addNode({
        id: 'node1',
        type: 'start',
        position: { x: 0, y: 0 },
      });
    });
    
    expect(result.current.nodes['node1']).toBeDefined();
    expect(result.current.isDirty).toBe(true);
  });
});
```

## Best Practices

1. **Separation of Concerns**: Keep technical concerns separate from business logic
2. **Type Safety**: Use branded types and type guards
3. **Immutability**: Use Immer for state updates
4. **Memoization**: Cache expensive computations
5. **Error Boundaries**: Wrap infrastructure calls in try-catch
6. **Service Abstraction**: Hide implementation details behind services
7. **Hook Composition**: Build complex hooks from simple ones

## Performance Optimization

### Store Optimization

```typescript
// Use shallow equality for performance
const selectedNodes = useUnifiedStore(
  useShallow(state => state.selectedNodeIds)
);

// Memoize expensive selectors
const expensiveData = useUnifiedStore(
  state => selectExpensiveData(state),
  shallow
);
```

### API Optimization

```typescript
// Batch GraphQL queries
const batchLink = new BatchHttpLink({
  uri: 'http://localhost:8000/graphql',
  batchInterval: 10,
  batchMax: 10,
});

// Cache strategies
const cache = new InMemoryCache({
  typePolicies: {
    Query: {
      fields: {
        diagrams: {
          merge(existing = [], incoming) {
            return [...existing, ...incoming];
          },
        },
      },
    },
  },
});
```

## Migration Guide

When adding new infrastructure:

1. **Create Service**:
   ```typescript
   // services/new-service.ts
   export class NewService {
     // Service methods
   }
   ```

2. **Add Store Slice** (if needed):
   ```typescript
   // store/slices/newSlice.ts
   export const createNewSlice = (set) => ({
     // State and actions
   });
   ```

3. **Create Hooks**:
   ```typescript
   // hooks/useNewFeature.ts
   export function useNewFeature() {
     // Hook implementation
   }
   ```

4. **Register Types**:
   ```typescript
   // types/index.ts
   export type NewID = Brand<string, 'NewID'>;
   ```

## Future Enhancements

- **Query Caching**: Persistent cache with IndexedDB
- **Optimistic Updates**: Immediate UI updates with rollback
- **WebSocket Manager**: Centralized WebSocket handling
- **Service Worker**: Offline support and caching
- **State Persistence**: Save state to localStorage
- **Time Travel Debugging**: Record and replay state changes
