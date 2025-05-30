// apps/web/src/stores/index.ts
// Centralized store exports

// Main consolidated stores
export { useConsolidatedDiagramStore } from './consolidatedDiagramStore';
export { useConsolidatedUIStore } from './consolidatedUIStore';
export { useExecutionStore } from './executionStore';
export { useHistoryStore } from './historyStore';

// Export consolidated types
export type { ConsolidatedDiagramState } from './consolidatedDiagramStore';
export type { ConsolidatedUIState } from './consolidatedUIStore';
export type { ExecutionState } from './executionStore';
export type { HistoryStore, HistoryState } from './historyStore';

// Hooks from other directories
export { useDiagramActions } from '@/features/diagram/hooks/useDiagramActions';
export { useHistoryActions } from '@/hooks/useHistoryActions';