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
export { default as DiagramCanvas } from '@/ui/components/diagram/DiagramCanvas';

/**
 * DiagramFileManager - Component for managing diagram file operations
 * Handles loading, saving, and listing diagram files
 */
export { DiagramFileManager } from '@/ui/components/diagram/DiagramFileManager';

/**
 * DiagramSidebar - Sidebar component with node palette
 * Used for displaying available node types that can be dragged onto the canvas
 */
export { DiagramSidebar } from '@/ui/components/diagram/sidebar/DiagramSidebar';


// Node Components
/**
 * Node-related exports for customization and extension
 */
export { BaseNode } from '@/ui/components/diagram/nodes/BaseNode';
export { default as ConfigurableNode } from '@/ui/components/diagram/nodes/ConfigurableNode';
export { default as PersonNode } from '@/ui/components/diagram/nodes/PersonNode';
export { default as nodeTypes } from '@/ui/components/diagram/nodes/nodeTypes';


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
export { useCanvasInteractions } from './hooks/ui';

// Operation hooks have been moved to @/infrastructure/store/hooks


// Types and Interfaces
/**
 * Core types for diagram structure and configuration
 */
export type {
  NodeConfigItem,
  NodeConfigs,
  FieldConfig,
  HandleConfig
} from './types/config';

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
} from '@/infrastructure/types/domain';


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
export type { DiagramSlice } from '@/infrastructure/store/slices/diagram';

// Context Re-exports
/**
 * Canvas context exports (moved to shared contexts)
 * These provide access to the canvas state and operations
 */
export {
  CanvasProvider,
  useCanvas,
  useCanvasState,
  useCanvasOperations,
  useIsCanvasReadOnly
} from '@/domain/diagram/contexts';


// ============================================
// Properties Editor Exports (Merged)
// ============================================

/**
 * PropertyPanel - The main properties editor panel component
 * Use this as the primary entry point for embedding the properties editor
 * Automatically syncs with selected nodes in the diagram
 */
export { PropertyPanel } from '@/ui/components/diagram/properties/PropertyPanel';

/**
 * PropertiesTab - Tab component for organizing property sections
 * Used within PropertyPanel to group related properties
 */
export { PropertiesTab } from '@/ui/components/diagram/properties/PropertiesTab';

/**
 * Unified form field component for property editing
 * Automatically renders the appropriate field type based on configuration
 */
export { UnifiedFormField } from '@/ui/components/diagram/properties/fields';

/**
 * Core form components for building custom property forms
 */
export * from '@/ui/components/diagram/properties/fields/FormComponents';

/**
 * usePropertyManager - Main hook for property management
 * Provides methods for reading and updating node properties
 * Handles validation and change propagation
 */
export { usePropertyManager } from './hooks/usePropertyManager';

/**
 * Core types for property forms and field configuration
 */
export type {
  PropertyFieldType,
  FormFieldConfig
} from './types/form';

/**
 * Re-export validation types from core
 */
export type { ValidationResult, FieldType } from '@/infrastructure/types/panel';

/**
 * Panel configurations for specific entity types
 * Use these for customizing property panels for arrows and persons
 */
export {
  ArrowPanelConfig,
  PersonPanelConfig,
  arrowFields,
  personFields,
  ENTITY_PANEL_CONFIGS
} from './config';
