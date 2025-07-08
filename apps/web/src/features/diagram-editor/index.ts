/**
 * Diagram Editor Feature - Public API
 * 
 * This feature provides the visual diagram editing capabilities for DiPeO,
 * including node creation, connection management, and diagram serialization.
 */


// Main Components
/**
 * DiagramCanvas - The main canvas component for diagram editing
 * Use this as the primary entry point for embedding the diagram editor
 */
export { default as DiagramCanvas } from './components/DiagramCanvas';

/**
 * DiagramFileManager - Component for managing diagram file operations
 * Handles loading, saving, and listing diagram files
 */
export { DiagramFileManager } from './components/DiagramFileManager';

/**
 * DiagramSidebar - Sidebar component with node palette
 * Used for displaying available node types that can be dragged onto the canvas
 */
export { DiagramSidebar } from './components/sidebar/DiagramSidebar';


// Node Components
/**
 * Node-related exports for customization and extension
 */
export { BaseNode } from './components/nodes/BaseNode';
export { default as ConfigurableNode } from './components/nodes/ConfigurableNode';
export { default as PersonNode } from './components/nodes/PersonNode';
export { default as nodeTypes } from './components/nodes/nodeTypes';


// Hooks
/**
 * useDiagramManager - Main hook for diagram management operations
 * Provides methods for loading, saving, and manipulating diagrams
 */
export { useDiagramManager } from './hooks/useDiagramManager';

/**
 * useDiagramLoader - Hook for loading diagram data
 * Handles async loading and error states
 */
export { useDiagramLoader } from './hooks/useDiagramLoader';

/**
 * useFileOperations - Hook for file-related operations
 * Provides methods for reading and writing diagram files
 */
export { useFileOperations } from './hooks/useFileOperations';

/**
 * Canvas interaction hooks for fine-grained control
 */
export { useCanvas, useCanvasInteractions } from './hooks/ui';

/**
 * Operation hooks for specific node types
 */
export { useNodeOperations, useArrowOperations, usePersonOperations } from './hooks/operations';


// Types and Interfaces
/**
 * Core types for diagram structure and configuration
 */
export type {
  NodeConfigItem,
  NodeConfigs,
  FieldConfig,
  HandleConfig
} from './types';

/**
 * Re-export core domain types that are commonly used
 */
export type {
  NodeType,
  DiagramFormat,
  DomainNode,
  DomainArrow,
  DomainDiagram,
  NodeID,
  ArrowID
} from '@/core/types/domain';


// Utilities
/**
 * Diagram serialization utilities
 * Use these for converting between diagram formats
 */
export {
  serializeDiagram,
  type SerializedDiagram
} from './utils/diagramSerializer';

/**
 * Handle index utilities for managing connection points
 */
export { 
  createHandleIndex, 
  getHandlesForNode 
} from './utils/handleIndex';


// Store Exports
/**
 * Zustand store slices for diagram state management
 * Only use these if you need direct store access
 */
export type { DiagramSlice } from './store';

// Context Re-exports
/**
 * Canvas context exports (moved to shared contexts)
 * These provide access to the canvas state and operations
 */
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
