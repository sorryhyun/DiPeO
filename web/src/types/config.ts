/**
 * Configuration-related types for the DiPeO application
 * These types define the structure of node configurations, handle configurations,
 * and form field configurations used throughout the visual programming interface.
 */

/**
 * Configuration for a node handle (connection point)
 */
export interface HandleConfig {
  id: string;
  position: 'top' | 'right' | 'bottom' | 'left';
  label?: string;
  offset?: { x: number; y: number };
  color?: string;
}

/**
 * Configuration for form fields in node property panels
 */
export interface FieldConfig {
  name: string;
  type: 'string' | 'number' | 'select' | 'textarea' | 'person' | 'boolean';
  label: string;
  required?: boolean;
  placeholder?: string;
  options?: { value: string; label: string }[];
  min?: number;
  max?: number;
  multiline?: boolean;
}

/**
 * Complete configuration for a node type
 */
export interface NodeConfigItem {
  label: string;
  icon: string;
  color: string;
  handles: {
    input?: HandleConfig[];
    output?: HandleConfig[];
  };
  fields: FieldConfig[];
  defaults: Record<string, any>;
}

/**
 * Type alias for node configuration mapping
 */
export type NodeConfigs = Record<string, NodeConfigItem>;