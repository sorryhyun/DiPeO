// Import slices from their feature locations
export { createDiagramSlice, type DiagramSlice } from '@/features/diagram-editor/store/diagramSlice';
export { createExecutionSlice, type ExecutionSlice } from '@/features/execution-monitor/store/executionSlice';
export { createPersonSlice, type PersonSlice } from '@/features/person-management/store/personSlice';

// Core slices
export { createComputedSlice, type ComputedSlice } from './computedSlice';
export { createUISlice, type UISlice } from './uiSlice';