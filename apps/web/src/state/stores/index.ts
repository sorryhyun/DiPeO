// apps/web/src/stores/index.ts

// New simplified stores
export { useDiagramStore } from './diagramStore';
export { useAppStore } from './appStore';
export { useApiKeyStore } from './apiKeyStore';
export { useExecutionStore } from './executionStore';
export { useConsolidatedUIStore } from './consolidatedUIStore';
export { useHistoryStore } from './historyStore';

// Export types
export type { Node, Arrow, Person } from '../../types';
export type { ApiKeyState } from './apiKeyStore';
export type { ExecutionState } from './executionStore';
export type { ConsolidatedUIState } from './consolidatedUIStore';
export type { HistoryStore, HistoryState } from './historyStore';
export type { DiagramStore } from './diagramStore';

// Hooks
export { useHistoryActions } from '../hooks/useHistoryActions';