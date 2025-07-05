// Diagram Editor Feature
export * from './components';
export * from './hooks';
export * from './store';

// Context exports moved to @/shared/contexts
export {
  CanvasProvider,
  useCanvasContext,
  useCanvasUIState,
  useCanvasOperationsContext,
  useCanvasSelection,
  useCanvasReadOnly,
  useCanvasDiagramData,
  useCanvasExecutionState,
  useCanvasStore,
  useCanvasPersons
} from '@/shared/contexts/CanvasContext';

// Main component exports
export { default as DiagramCanvas } from './components/DiagramCanvas';
export { DiagramFileManager } from './components/DiagramFileManager';
