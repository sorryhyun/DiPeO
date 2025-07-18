/**
 * Execution Monitor Feature - Public API
 * 
 * This feature provides real-time monitoring and control of diagram execution,
 * including execution state visualization, interactive prompts, and debugging tools.
 */

// ============================================
// Main Components
// ============================================

/**
 * ExecutionView - The main execution monitoring component
 * Displays real-time execution status, logs, and results
 */
export { ExecutionView } from './components/ExecutionView';

/**
 * ExecutionControls - Control panel for execution operations
 * Provides start, stop, pause, and step-through controls
 */
export { ExecutionControls } from './components/ExecutionControls';

/**
 * ExecutionOrderView - Visualizes the execution order of nodes
 * Shows the planned execution sequence before running
 */
export { ExecutionOrderView } from './components/ExecutionOrderView';

/**
 * InteractivePromptModal - Modal for handling user interaction during execution
 * Used when nodes require user input during runtime
 */
export { InteractivePromptModal } from './components/InteractivePromptModal';

// ============================================
// Hooks
// ============================================

/**
 * useExecution - Main hook for execution control
 * Provides methods to start, stop, and monitor execution
 */
export { useExecution } from './hooks/useExecution';

/**
 * useExecutionState - Hook for accessing current execution state
 * Returns real-time execution status and node states
 */
export { useExecutionState } from './hooks/useExecutionState';

/**
 * useExecutionData - Hook for accessing execution results and logs
 * Provides access to execution history and output data
 */
export { useExecutionData } from './hooks/useExecutionData';

/**
 * useExecutionUpdates - Hook for subscribing to execution updates
 * Provides real-time updates via WebSocket connection
 */
export { useExecutionUpdates } from './hooks/useExecutionUpdates';

/**
 * useExecutionOrder - Hook for computing execution order
 * Analyzes diagram topology to determine execution sequence
 */
export { useExecutionOrder } from './hooks/useExecutionOrder';

/**
 * useMonitorMode - Hook for monitor mode functionality
 * Enables read-only execution monitoring without control
 */
export { useMonitorMode } from './hooks/useMonitorMode';

/**
 * useExecutionGraphQL - Hook for GraphQL execution operations
 * Low-level hook for custom execution queries and mutations
 */
export { useExecutionGraphQL } from './hooks/useExecutionGraphQL';

// ============================================
// Types and Interfaces
// ============================================

/**
 * Core execution types
 */
export type {
  ExecutionStatus,
  NodeExecutionStatus,
  PersonMemoryState,
  TokenUsage,
  InteractivePromptData
} from './types/execution';

/**
 * Re-export domain execution types
 */
export type {
  ExecutionState,
  NodeState,
  ExecutionUpdate
} from '@/core/types/domain';

/**
 * Message types for execution communication
 */
export type {
  ConversationFilters,
  UIConversationMessage
} from './types/message';

/**
 * Store types for state management
 */
export type { ExecutionSlice } from './store';

// ============================================
// Utilities
// ============================================

/**
 * Execution helper utilities
 */
export {
  formatTime,
  getNodeIcon,
  getNodeColor
} from './utils/executionHelpers';