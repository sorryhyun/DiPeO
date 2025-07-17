import { StateCreator, StoreMutatorIdentifier } from 'zustand';

type Logger = <
  T,
  Mps extends [StoreMutatorIdentifier, unknown][] = [],
  Mcs extends [StoreMutatorIdentifier, unknown][] = []
>(
  f: StateCreator<T, Mps, Mcs>,
  name?: string
) => StateCreator<T, Mps, Mcs>;

type LoggerImpl = <T>(
  f: StateCreator<T, [], []>,
  name?: string
) => StateCreator<T, [], []>;

// Debugging middleware for store slice interactions
const loggerImpl: LoggerImpl = (f, name) => (set, get, store) => {
  const loggedSet = ((...args: any[]) => {
    const previousState = get();
    
    // Call the actual set function
    // @ts-expect-error - Zustand's overloaded set function types are complex
    set(...args);
    
    const nextState = get();
    
    // Log state changes in development
    if (import.meta.env.DEV) {
      const stateDiff = getStateDiff(previousState, nextState);
      
      if (Object.keys(stateDiff).length > 0) {
        console.group(`[${name || 'Store'}] State Update`);
        console.log('Previous:', previousState);
        console.log('Changes:', stateDiff);
        console.log('Next:', nextState);
        
        // Detect cross-slice violations
        detectCrossSliceViolations(stateDiff, name);
        
        console.groupEnd();
      }
    }
  }) as typeof set;
  
  return f(loggedSet, get, store);
};

// Helper to get state differences
function getStateDiff(prev: any, next: any): Record<string, any> {
  const diff: Record<string, any> = {};
  
  // Check for changed properties
  for (const key in next) {
    if (prev[key] !== next[key]) {
      diff[key] = {
        prev: prev[key],
        next: next[key]
      };
    }
  }
  
  // Check for removed properties
  for (const key in prev) {
    if (!(key in next)) {
      diff[key] = {
        prev: prev[key],
        next: undefined
      };
    }
  }
  
  return diff;
}

// Detect cross-slice violations
function detectCrossSliceViolations(diff: Record<string, any>, sliceName?: string) {
  // Operations that are allowed to modify multiple slices
  const allowedCrossSliceOperations = [
    'UnifiedStore', // The unified store itself can modify any slice
    'clearAll',     // Clear all operation needs to modify multiple slices
    'transaction',  // Transactions may modify multiple slices
    'undo',         // Undo operations restore multiple slices
    'redo'          // Redo operations restore multiple slices
  ];
  
  // Skip violation detection for allowed operations
  if (sliceName && allowedCrossSliceOperations.includes(sliceName)) {
    return;
  }
  
  const sliceBoundaries = {
    diagram: ['nodes', 'arrows', 'diagramName', 'diagramDescription', 'diagramId', 'diagramFormat'],
    execution: ['execution'],
    person: ['persons'],
    ui: [
      'selectedId', 'selectedType', 'multiSelectedIds', 'highlightedPersonId',
      'activeView', 'activeCanvas', 'dashboardTab', 'zoom', 'position',
      'readOnly', 'executionReadOnly', 'isMonitorMode', 'canvasMode'
    ],
    computed: ['dataVersion'],
    history: ['history'],
    // UnifiedStore's own properties
    unified: ['handles', 'handleIndex']
  };
  
  // Determine which slice is being modified
  const modifiedSlices = new Set<string>();
  
  for (const key of Object.keys(diff)) {
    for (const [slice, properties] of Object.entries(sliceBoundaries)) {
      if (properties.includes(key)) {
        modifiedSlices.add(slice);
      }
    }
  }
  
  // Warn if multiple slices are modified
  if (modifiedSlices.size > 1) {
    console.warn(
      `⚠️ Cross-slice violation detected!`,
      `Slice "${sliceName}" is modifying properties from multiple slices:`,
      Array.from(modifiedSlices),
      `Modified properties:`, Object.keys(diff)
    );
  }
  
  // Specific violation checks
  if (sliceName === 'execution' && 'activeView' in diff) {
    console.warn(
      `⚠️ Slice isolation violation: ExecutionSlice should not directly modify UI state.`,
      `Use events or actions to communicate between slices.`
    );
  }
}

export const logger = loggerImpl as Logger;

// Event emitter for inter-slice communication
export class StoreEventEmitter extends EventTarget {
  emit(eventType: string, detail?: any) {
    this.dispatchEvent(new CustomEvent(eventType, { detail }));
  }
}

export const storeEvents = new StoreEventEmitter();

// Event types for inter-slice communication
export const STORE_EVENTS = {
  EXECUTION_STARTED: 'execution:started',
  EXECUTION_STOPPED: 'execution:stopped',
  SWITCH_TO_EXECUTION_VIEW: 'ui:switchToExecutionView',
  PERSON_CREATED: 'person:created',
  NODE_SELECTED: 'node:selected',
} as const;