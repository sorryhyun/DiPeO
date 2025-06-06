// Consolidated stores (Phase 3: State Simplification)
export { useDiagramStore } from './diagramStore';
export { useExecutionStore } from './executionStore';
export { useUIStore, useConsolidatedUIStore } from './uiStore';

// Legacy stores (to be phased out)
export { useAppStore } from './appStore';
export { useApiKeyStore } from './apiKeyStore';
export { useHistoryStore } from './historyStore';

// Export types
export type { DiagramStore } from './diagramStore';
export type { ExecutionStore } from './executionStore';
export type { UIStore } from './uiStore';

// Legacy types (to be phased out)
export type { ApiKeyState } from './apiKeyStore';
export type { HistoryStore, HistoryState } from './historyStore';

// Hooks
export { useHistoryActions } from '../hooks/useHistoryActions';