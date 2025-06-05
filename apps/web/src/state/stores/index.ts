// apps/web/src/stores/index.ts
// Centralized store exports

// Main stores
export { useConsolidatedUIStore } from './consolidatedUIStore';
export { useExecutionStore } from './executionStore';
export { useHistoryStore } from './historyStore';

// Individual stores (new modular architecture)
export { useApiKeyStore } from './apiKeyStore';
export { useDiagramStore } from './diagramStore';

// Export types
export type { ConsolidatedUIState } from './consolidatedUIStore';
export type { ExecutionState } from './executionStore';
export type { HistoryStore, HistoryState } from './historyStore';

// Export individual store types
export type { ApiKeyState } from './apiKeyStore';
export type { DiagramStore } from './diagramStore';

// Hooks from other directories
// export { useDiagramActions } from '@/features/diagram/hooks/useDiagramActions'; // Removed - use direct imports from io hooks
export { useHistoryActions } from '@/state/hooks/useHistoryActions';