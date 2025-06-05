// apps/web/src/stores/index.ts
// Simplified store exports - Phase 2 refactoring

// New simplified stores
export { useDiagramStore } from './diagramStore';
export { useAppStore } from './appStore';
export { useApiKeyStore } from './apiKeyStore';

// Export types
export type { Node, Arrow, Person } from './diagramStore';
export type { ApiKeyState } from './apiKeyStore';

// Legacy stores (to be removed)
export { useConsolidatedUIStore } from './consolidatedUIStore';
export { useExecutionStore } from './executionStore';
export { useHistoryStore } from './historyStore';

// Legacy types (to be removed)
export type { ConsolidatedUIState } from './consolidatedUIStore';
export type { ExecutionState } from './executionStore';
export type { HistoryStore, HistoryState } from './historyStore';

// Hooks
export { useHistoryActions } from '@/state/hooks/useHistoryActions';