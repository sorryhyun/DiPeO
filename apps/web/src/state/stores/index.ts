// apps/web/src/stores/index.ts

// New simplified stores
export { useDiagramStore } from './diagramStore';
export { useAppStore } from './appStore';
export { useApiKeyStore } from './apiKeyStore';

// Export types
export type { Node, Arrow, Person } from './diagramStore';
export type { ApiKeyState } from './apiKeyStore';

// Hooks
export { useHistoryActions } from '@/state/hooks/useHistoryActions';