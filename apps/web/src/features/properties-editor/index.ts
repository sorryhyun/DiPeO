/**
 * Properties Editor Feature - Public API
 * 
 * This feature provides the property editing interface for DiPeO nodes,
 * allowing users to configure node parameters, view node details, and
 * manage node-specific settings.
 */

// ============================================
// Main Components
// ============================================

/**
 * PropertyPanel - The main properties editor panel component
 * Use this as the primary entry point for embedding the properties editor
 * Automatically syncs with selected nodes in the diagram
 */
export { PropertyPanel } from './components/PropertyPanel';

/**
 * PropertiesTab - Tab component for organizing property sections
 * Used within PropertyPanel to group related properties
 */
export { PropertiesTab } from './components/PropertiesTab';

// ============================================
// Field Components
// ============================================

/**
 * Unified form field component for property editing
 * Automatically renders the appropriate field type based on configuration
 */
export { UnifiedFormField } from './components/fields';

/**
 * Core form components for building custom property forms
 */
export * from './components/fields/FormComponents';

// ============================================
// Hooks
// ============================================

/**
 * usePropertyManager - Main hook for property management
 * Provides methods for reading and updating node properties
 * Handles validation and change propagation
 */
export { usePropertyManager } from './hooks/usePropertyManager';

// ============================================
// Types and Interfaces
// ============================================

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
export type { ValidationResult, FieldType } from '@/core/types/panel';

// ============================================
// Configuration Exports
// ============================================

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