// ===== CONSOLIDATED HOOKS =====
// Master diagram hook - combines all functionalities
export * from './useDiagram';

// Domain-specific store selectors
export * from './store';

// Consolidated functionality hooks
export * from './usePropertyManager';
export * from './useFileOperations';
export * from './useRealtimeExecution';
export * from './useCanvasInteractions';

// ===== REMAINING HOOKS =====
// Store selectors (main hooks - keep for gradual migration)
export * from './useStoreSelectors';

// Conversation hooks
export * from './useConversationData';

// Node hooks
export * from './useNodeType';

// Properties hooks  
export * from './useApiKeys';

// Runtime hooks
export * from './useDiagramRunner';

// Store hooks
export * from './useHistoryActions';