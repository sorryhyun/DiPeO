/**
 * Focused selector hooks for efficient state access
 * These hooks replace repetitive useShallow patterns with specialized selectors
 */

// Diagram data selectors
export {
  useDiagramData,
  useNodeData,
  useArrowData,
  useNodesByType,
  useDiagramVersion
} from './useDiagramData';

// Execution data selectors
export {
  useExecutionData,
  useIsNodeRunning,
  useNodeExecutionState,
  useRunningNodeIds,
  useExecutionContextValue,
  useIsExecuting
} from './useExecutionData';

// UI state selectors
export {
  useUIState,
  useSelection,
  useIsSelected,
  useReadOnlyState,
  useModalStates
} from './useUIState';

// Persons data selectors
export {
  usePersonsData,
  usePersonData,
  useIsPersonInUse,
  usePersonsByService,
  usePersonUsageStats
} from './usePersonsData';