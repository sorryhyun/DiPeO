import type {
  NodeID,  ArrowID,  PersonID,  HandleID,  ApiKeyID,
  DomainNode,  DomainArrow,  DomainPerson,  DomainHandle,  DomainApiKey,
  NodeKind,  Vec2,  LLMService,} from '@/types';

// Define NodeState locally as it's not exported from types
export interface NodeState {
  status: 'pending' | 'running' | 'completed' | 'failed' | 'skipped';
  error?: string;
  timestamp: number;
}

// History types
export interface Snapshot {
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  persons: Map<PersonID, DomainPerson>;
  handles: Map<HandleID, DomainHandle>;
  apiKeys: Map<ApiKeyID, DomainApiKey>;
  timestamp: number;
}

interface Transaction {
  id: string;
  changes: any[];
  timestamp: number;
}

// Unified store interface
export interface UnifiedStore {
  // === Core Data ===
  nodes: Map<NodeID, DomainNode>;
  arrows: Map<ArrowID, DomainArrow>;
  persons: Map<PersonID, DomainPerson>;
  handles: Map<HandleID, DomainHandle>;
  apiKeys: Map<ApiKeyID, DomainApiKey>;
  
  // === UI State ===
  selectedId: NodeID | ArrowID | PersonID | null;
  selectedType: 'node' | 'arrow' | 'person' | null;
  activeView: 'diagram' | 'execution';
  activeCanvas: 'main' | 'execution' | 'memory';
  dashboardTab: string;
  readOnly: boolean;
  showApiKeysModal: boolean;
  showExecutionModal: boolean;
  
  // === Execution State ===
  execution: {
    id: string | null;
    isRunning: boolean;
    runningNodes: Set<NodeID>;
    nodeStates: Map<NodeID, NodeState>;
    context: Record<string, unknown>;
  };
  
  // === History ===
  history: {
    undoStack: Snapshot[];
    redoStack: Snapshot[];
    currentTransaction: Transaction | null;
  };
  
  // === Actions (single source of truth) ===
  // Node operations
  addNode: (type: NodeKind, position: Vec2, initialData?: Record<string, unknown>) => NodeID;
  updateNode: (id: NodeID, updates: Partial<DomainNode>) => void;
  deleteNode: (id: NodeID) => void;
  
  // Arrow operations
  addArrow: (source: HandleID, target: HandleID, data?: Record<string, unknown>) => ArrowID;
  updateArrow: (id: ArrowID, updates: Partial<DomainArrow>) => void;
  deleteArrow: (id: ArrowID) => void;
  
  // Person operations
  addPerson: (name: string, service: LLMService, model: string) => PersonID;
  updatePerson: (id: PersonID, updates: Partial<DomainPerson>) => void;
  deletePerson: (id: PersonID) => void;
  
  // Selection
  select: (id: string, type: 'node' | 'arrow' | 'person') => void;
  clearSelection: () => void;
  
  // UI State
  setActiveCanvas: (canvas: 'main' | 'execution' | 'memory') => void;
  setReadOnly: (readOnly: boolean) => void;
  setDashboardTab: (tab: string) => void;
  openApiKeysModal: () => void;
  closeApiKeysModal: () => void;
  openExecutionModal: () => void;
  closeExecutionModal: () => void;
  
  // API Key operations
  addApiKey: (name: string, service: string) => ApiKeyID;
  updateApiKey: (id: ApiKeyID, updates: Partial<DomainApiKey>) => void;
  deleteApiKey: (id: ApiKeyID) => void;
  
  // Execution
  startExecution: (executionId: string) => void;
  updateNodeExecution: (nodeId: NodeID, state: NodeState) => void;
  stopExecution: () => void;
  
  // History
  undo: () => void;
  redo: () => void;
  
  // Transactions
  transaction: <T>(fn: () => T) => T;
  
  // Utilities
  createSnapshot: () => Snapshot;
  restoreSnapshot: (snapshot: Snapshot) => void;
}
