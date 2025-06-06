// Configuration-specific types
import type { NodeType } from '@/types';

export interface HandleConfig {
  id: string;
  position: 'top' | 'right' | 'bottom' | 'left';
  label?: string;
  offset?: { x: number; y: number };
}

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