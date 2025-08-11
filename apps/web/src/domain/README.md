# DiPeO Frontend Domain Layer

## Overview

The `apps/web/src/domain` directory contains the **business logic and domain-specific functionality** of the DiPeO web application. Following Domain-Driven Design (DDD) principles, this layer encapsulates business rules, domain models, and operations organized by bounded contexts.

## Architecture

### Domain-Driven Structure

```
┌─────────────────────────────────────┐
│         UI Layer                    │
│     (React Components)              │
└────────────┬────────────────────────┘
             │ Uses
    ┌────────▼────────────┐
    │   Domain Layer      │ ◄── Business Logic
    │  (This Directory)   │
    ├─────────────────────┤
    │ • Diagram Domain    │
    │ • Execution Domain  │
    │ • Person Domain     │
    │ • Conversation      │
    └────────┬────────────┘
             │ Uses
    ┌────────▼────────────┐
    │ Infrastructure Layer│ ◄── Technical Services
    │  (Store, API, etc.) │
    └─────────────────────┘
```

### Domain Organization

```
domain/
├── diagram/              # Diagram editing & properties
│   ├── hooks/           # Diagram-specific React hooks
│   ├── services/        # Business logic services
│   ├── config/          # Node configurations
│   ├── types/           # Domain types
│   ├── utils/           # Domain utilities
│   ├── contexts/        # React contexts
│   ├── forms/           # Form utilities
│   └── adapters/        # Domain adapters
└── execution/           # Execution monitoring
    ├── hooks/           # Execution hooks
    ├── services/        # Execution services
    ├── types/           # Execution types
    ├── utils/           # Execution utilities
    └── config/          # Execution config
```

## Domain Modules

### 1. Diagram Domain (`/diagram/`)

Handles all diagram-related business logic:

#### Core Responsibilities
- **Node Management**: Creation, configuration, validation
- **Connection Logic**: Edge validation, handle management
- **Property Editing**: Dynamic form generation, validation
- **Person Management**: AI persona configuration
- **File Operations**: Save, load, export diagrams

#### Key Components

**Hooks** (`hooks/`):
```typescript
// Main diagram management
export function useDiagramManager(options?: UseDiagramManagerOptions) {
  // Comprehensive diagram operations
  return {
    // State
    isEmpty, isDirty, canExecute,
    nodeCount, arrowCount, personCount,
    
    // Operations
    newDiagram, saveDiagram, loadDiagramFromFile,
    exportDiagram, importDiagram,
    
    // Execution
    executeDiagram, stopExecution, isExecuting,
    
    // Validation
    validateDiagram,
    
    // History
    undo, redo, canUndo, canRedo,
    
    // Analytics
    getDiagramStats
  };
}

// Property panel management
export function usePropertyManager() {
  return {
    selectedNodes, selectedEdges,
    updateNodeData, updateEdgeData,
    deleteSelected, duplicateSelected,
    getFieldConfig, validateField
  };
}

// Canvas interactions
export function useCanvas({ readOnly }: UseCanvasOptions) {
  return {
    nodes, edges,
    addNode, updateNode, deleteNode,
    addEdge, updateEdge, deleteEdge,
    viewport, setViewport,
    fitView, zoomIn, zoomOut
  };
}
```

**Configuration** (`config/`):
```typescript
// Node registry and configurations
export const nodeRegistry = {
  person_job: {
    type: 'person_job',
    label: 'Person Job',
    category: 'Core',
    icon: '👤',
    fields: [
      { name: 'person_id', type: 'person_select', required: true },
      { name: 'prompt', type: 'text', required: true },
      { name: 'model', type: 'model_select' }
    ]
  },
  // ... more node types
};

// Field configurations with dynamic behavior
export const fieldConfigs = {
  person_select: {
    component: PersonSelectField,
    validator: validatePersonId,
    placeholder: 'Select a person...'
  },
  // ... more field types
};
```

**Services** (`services/`):
```typescript
class DiagramService {
  // Diagram operations
  async saveDiagram(diagram: DomainDiagram): Promise<void>;
  async loadDiagram(id: string): Promise<DomainDiagram>;
  async exportToFormat(diagram: DomainDiagram, format: DiagramFormat): Promise<string>;
  
  // Validation
  validateStructure(diagram: DomainDiagram): ValidationResult;
  validateConnections(edges: Edge[]): ConnectionError[];
  
  // Transformations
  optimizeDiagram(diagram: DomainDiagram): DomainDiagram;
  convertFormat(diagram: any, from: DiagramFormat, to: DiagramFormat): any;
}
```

**Forms** (`forms/`):
```typescript
// Form field utilities
export const formUtils = {
  // Dynamic field generation
  generateFieldsForNode(nodeType: string): FormField[];
  
  // Validation
  validateField(field: FormField, value: any): ValidationError | null;
  
  // Transformations
  serializeFormData(data: FormData): NodeProperties;
  deserializeNodeData(node: Node): FormData;
};

// Validation rules
export const validators = {
  required: (value: any) => !value ? 'This field is required' : null,
  minLength: (min: number) => (value: string) => 
    value.length < min ? `Minimum ${min} characters` : null,
  pattern: (regex: RegExp, message: string) => (value: string) =>
    !regex.test(value) ? message : null
};
```

**Types** (`types/`):
```typescript
// Domain models
export interface NodeConfigItem {
  type: string;
  label: string;
  category: 'Core' | 'Control' | 'Data' | 'Integration';
  icon?: string;
  fields: FieldConfig[];
  validation?: ValidationRule[];
  handles?: HandleConfig[];
}

export interface PanelState {
  selectedNodeIds: string[];
  selectedEdgeIds: string[];
  activeTab: 'properties' | 'settings' | 'people';
  formData: Record<string, any>;
  validation: Record<string, ValidationError>;
}

export interface DiagramFormData {
  nodes: Record<string, NodeFormData>;
  edges: Record<string, EdgeFormData>;
  metadata: DiagramMetadata;
}
```

### 2. Execution Domain (`/execution/`)

Manages diagram execution and monitoring:

#### Core Responsibilities
- **Execution Control**: Start, stop, pause, resume
- **Real-time Monitoring**: Node states, progress, logs
- **GraphQL Subscriptions**: Live updates via subscriptions
- **Conversation Tracking**: LLM interactions
- **Error Handling**: Execution failures and recovery

#### Key Components

**Hooks** (`hooks/`):
```typescript
// Main execution hook
export function useExecution(options?: UseExecutionOptions) {
  return {
    // State
    execution: currentExecutionState,
    nodeStates: recordOfNodeStates,
    isRunning, progress, duration,
    
    // Actions
    execute: (diagram, options) => Promise<void>,
    connectToExecution: (executionId) => void,
    abort: () => void,
    
    // Node control
    pauseNode, resumeNode, skipNode,
    
    // Interactive prompts
    interactivePrompt: currentPrompt,
    respondToPrompt: (response) => void,
    
    // Helpers
    formatTime, getNodeIcon, getNodeColor
  };
}

// GraphQL-based execution
export function useExecutionGraphQL() {
  return {
    startExecution: (diagram, variables) => Promise<ExecutionResult>,
    subscribeToUpdates: (executionId) => Observable<ExecutionUpdate>,
    getExecutionStatus: (executionId) => Promise<ExecutionStatus>
  };
}

// Streaming updates
export function useExecutionStreaming(executionId: string) {
  return {
    updates: StreamedUpdate[],
    isConnected: boolean,
    error: Error | null,
    reconnect: () => void
  };
}

// Monitor mode for CLI integration
export function useMonitorMode() {
  const [isMonitorMode, setMonitorMode] = useState(false);
  
  useEffect(() => {
    // Check URL params for monitor=true
    const params = new URLSearchParams(window.location.search);
    setMonitorMode(params.get('monitor') === 'true');
  }, []);
  
  return {
    isMonitorMode,
    autoConnect: isMonitorMode,
    showFullScreen: isMonitorMode
  };
}
```

**Types** (`types/`):
```typescript
// Execution models
export interface ExecutionState {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'aborted';
  startTime: Date;
  endTime?: Date;
  currentNode?: string;
  progress: number;
  error?: ExecutionError;
}

export interface NodeExecutionState {
  nodeId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  startTime?: Date;
  endTime?: Date;
  output?: any;
  error?: string;
  retryCount: number;
}

export interface ExecutionUpdate {
  type: EventType;
  nodeId?: string;
  data?: any;
  timestamp: Date;
}

// Message types for conversations
export interface ConversationMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
  metadata?: {
    model?: string;
    tokens?: number;
    nodeId?: string;
  };
}
```

**Services** (`services/`):
```typescript
class ExecutionService {
  // Execution control
  async startExecution(diagram: DomainDiagram, options: ExecutionOptions): Promise<string>;
  async stopExecution(executionId: string): Promise<void>;
  
  // Monitoring
  subscribeToExecution(executionId: string): Observable<ExecutionUpdate>;
  async getExecutionHistory(diagramId: string): Promise<ExecutionRecord[]>;
  
  // Analytics
  async getExecutionMetrics(executionId: string): Promise<ExecutionMetrics>;
  calculateBottlenecks(execution: ExecutionState): BottleneckAnalysis;
}
```

**Utils** (`utils/`):
```typescript
// Execution helpers
export const executionHelpers = {
  // Format execution time
  formatDuration: (start: Date, end?: Date) => string;
  
  // Calculate progress
  calculateProgress: (completed: number, total: number) => number;
  
  // Node status helpers
  getNodeStatusColor: (status: NodeExecutionStatus) => string;
  getNodeStatusIcon: (status: NodeExecutionStatus) => string;
  
  // Error formatting
  formatExecutionError: (error: ExecutionError) => string;
};
```

## Domain Patterns

### 1. Hook Composition

Domain hooks compose infrastructure hooks:

```typescript
// Domain hook uses infrastructure
function useDiagramManager() {
  // Infrastructure hooks
  const store = useUnifiedStore();
  const { data } = useQuery(GET_DIAGRAM);
  const [saveMutation] = useMutation(SAVE_DIAGRAM);
  
  // Domain logic
  const validateDiagram = () => {
    // Business validation rules
  };
  
  const calculateStats = () => {
    // Domain-specific calculations
  };
  
  return {
    // Expose domain operations
    diagram: store.diagram,
    save: () => saveMutation({ variables: store.diagram }),
    validate: validateDiagram,
    stats: calculateStats()
  };
}
```

### 2. Service Layer

Services encapsulate complex business logic:

```typescript
class DiagramValidationService {
  // Pure business logic
  validateNodeConnections(nodes: Node[], edges: Edge[]): ValidationResult {
    const errors = [];
    
    // Business rule: Start nodes can't have inputs
    const startNodes = nodes.filter(n => n.type === 'start');
    for (const start of startNodes) {
      const hasInput = edges.some(e => e.target === start.id);
      if (hasInput) {
        errors.push({
          nodeId: start.id,
          message: 'Start nodes cannot have inputs'
        });
      }
    }
    
    return { isValid: errors.length === 0, errors };
  }
}
```

### 3. Configuration-Driven

Node behavior defined by configuration:

```typescript
// Node configuration drives UI generation
const nodeConfig = {
  type: 'api_job',
  fields: [
    {
      name: 'endpoint',
      type: 'url',
      required: true,
      validation: {
        pattern: /^https?:\/\/.+/,
        message: 'Must be a valid URL'
      }
    },
    {
      name: 'method',
      type: 'select',
      options: ['GET', 'POST', 'PUT', 'DELETE'],
      default: 'GET'
    }
  ]
};

// UI automatically generated from config
<ConfigurableNode config={nodeConfig} />
```

### 4. Domain Events

Domain operations emit events:

```typescript
// Domain event emitter
class DiagramEventEmitter extends EventEmitter {
  // Emit domain events
  onNodeAdded(node: Node) {
    this.emit('node:added', { node, timestamp: Date.now() });
  }
  
  onExecutionCompleted(result: ExecutionResult) {
    this.emit('execution:completed', result);
  }
}

// React to domain events
useEffect(() => {
  const handler = (event) => {
    // Handle domain event
    toast.success(`Node ${event.node.id} added`);
  };
  
  emitter.on('node:added', handler);
  return () => emitter.off('node:added', handler);
}, []);
```

## Integration Points

### With Infrastructure Layer

```typescript
// Domain uses infrastructure services
import { useUnifiedStore } from '@/infrastructure/store';
import { ConversionService } from '@/infrastructure/converters';
import { ValidationService } from '@/infrastructure/services';

function useDiagramOperations() {
  const store = useUnifiedStore();
  
  const convertDiagram = (format: DiagramFormat) => {
    // Use infrastructure converter
    return ConversionService.convertDiagram(store.diagram, format);
  };
  
  const validateField = (nodeType: string, field: string, value: any) => {
    // Use infrastructure validator
    return ValidationService.validateField(nodeType, field, value);
  };
}
```

### With UI Layer

```typescript
// UI components use domain hooks
import { useDiagramManager, usePropertyManager } from '@/domain/diagram';

function DiagramEditor() {
  const diagram = useDiagramManager();
  const properties = usePropertyManager();
  
  return (
    <div>
      <Canvas 
        nodes={diagram.nodes}
        onNodeClick={properties.selectNode}
      />
      <PropertiesPanel
        selectedNode={properties.selectedNode}
        onUpdate={properties.updateNodeData}
      />
    </div>
  );
}
```

## Testing Strategy

### Unit Testing

```typescript
// Test domain logic in isolation
describe('DiagramValidationService', () => {
  it('should validate start node connections', () => {
    const service = new DiagramValidationService();
    const nodes = [{ id: '1', type: 'start' }];
    const edges = [{ source: '2', target: '1' }]; // Invalid
    
    const result = service.validateNodeConnections(nodes, edges);
    
    expect(result.isValid).toBe(false);
    expect(result.errors[0].message).toContain('cannot have inputs');
  });
});
```

### Integration Testing

```typescript
// Test domain hooks with mocked infrastructure
describe('useDiagramManager', () => {
  it('should save diagram', async () => {
    const { result } = renderHook(() => useDiagramManager());
    
    await act(async () => {
      await result.current.saveDiagram('test.yaml');
    });
    
    expect(mockSaveMutation).toHaveBeenCalledWith({
      variables: expect.objectContaining({
        filename: 'test.yaml'
      })
    });
  });
});
```

## Best Practices

1. **Keep Domain Pure**: No UI concerns in domain layer
2. **Use Domain Language**: Name things using business terms
3. **Encapsulate Logic**: Complex rules in services, not components
4. **Compose Hooks**: Build complex hooks from simple ones
5. **Type Safety**: Strong typing for all domain models
6. **Validate Early**: Business validation in domain layer
7. **Document Rules**: Comment complex business logic

## Common Patterns

### Field Configuration

```typescript
// Dynamic field configuration
const fieldConfig = {
  person_select: {
    component: PersonSelectField,
    fetchOptions: async () => {
      const persons = await PersonService.getAll();
      return persons.map(p => ({
        value: p.id,
        label: p.name
      }));
    },
    validation: (value) => {
      if (!value) return 'Person is required';
      if (!PersonService.exists(value)) return 'Invalid person';
      return null;
    }
  }
};
```

### State Synchronization

```typescript
// Sync domain state with infrastructure
function useDiagramSync() {
  const diagram = useDiagramManager();
  const store = useUnifiedStore();
  
  // Sync on changes
  useEffect(() => {
    if (diagram.isDirty) {
      store.updateDiagram(diagram.data);
    }
  }, [diagram.isDirty]);
}
```

### Error Boundaries

```typescript
// Domain-specific error handling
class DiagramErrorBoundary extends ErrorBoundary {
  handleError(error: Error) {
    if (error instanceof DiagramValidationError) {
      // Handle domain error
      toast.error(`Diagram validation failed: ${error.message}`);
    } else {
      // Propagate unknown errors
      throw error;
    }
  }
}
```

## Migration Guide

When adding new domain functionality:

1. **Create Domain Module**:
   ```
   domain/new-feature/
   ├── hooks/
   ├── services/
   ├── types/
   ├── utils/
   └── index.ts
   ```

2. **Define Domain Types**:
   ```typescript
   // types/index.ts
   export interface NewFeature {
     id: string;
     // Domain properties
   }
   ```

3. **Implement Business Logic**:
   ```typescript
   // services/index.ts
   export class NewFeatureService {
     // Business operations
   }
   ```

4. **Create React Hooks**:
   ```typescript
   // hooks/index.ts
   export function useNewFeature() {
     // Hook implementation
   }
   ```

5. **Export Public API**:
   ```typescript
   // index.ts
   export * from './hooks';
   export * from './types';
   export { NewFeatureService } from './services';
   ```

## Future Enhancements

- **Domain Events Bus**: Centralized event system
- **Saga Pattern**: Complex multi-step operations
- **CQRS**: Separate read/write models
- **Domain Validation DSL**: Declarative validation rules
- **Undo/Redo System**: Command pattern implementation
- **Collaborative Editing**: CRDT-based synchronization