// apps/web/src/stores/index.ts
// Centralized store exports

// Main stores
export { useConsolidatedUIStore } from './consolidatedUIStore';
export { useExecutionStore } from './executionStore';
export { useHistoryStore } from './historyStore';

// Individual stores (new modular architecture)
export { useNodeArrowStore } from './nodeArrowStore';
export { usePersonStore } from './personStore';
export { useApiKeyStore } from './apiKeyStore';
export { useMonitorStore } from './monitorStore';
export { useDiagramOperationsStore } from './diagramOperationsStore';

// Export types
export type { ConsolidatedUIState } from './consolidatedUIStore';
export type { ExecutionState } from './executionStore';
export type { HistoryStore, HistoryState } from './historyStore';

// Export individual store types
export type { NodeArrowState } from './nodeArrowStore';
export type { PersonState } from './personStore';
export type { ApiKeyState } from './apiKeyStore';
export type { MonitorState } from './monitorStore';
export type { DiagramOperationsState } from './diagramOperationsStore';

// Hooks from other directories
// export { useDiagramActions } from '@/features/diagram/hooks/useDiagramActions'; // Removed - use direct imports from serialization hooks
export { useHistoryActions } from '@/state/hooks/useHistoryActions';