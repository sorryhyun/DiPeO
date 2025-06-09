/**
 * Unified configuration system that combines node and panel configurations
 * This allows deriving panel configs from node configs automatically
 */

import type { NodeConfigItem, FieldConfig } from '@/types/config';
import type { TypedPanelConfig, TypedPanelFieldConfig, PanelFieldType } from '@/types/ui';

/**
 * Maps domain field types to panel field types
 */
const fieldTypeMapping: Record<FieldConfig['type'], PanelFieldType> = {
  string: 'text',
  number: 'text', // Will add number validation
  select: 'select',
  textarea: 'variableTextArea',
  person: 'personSelect',
  boolean: 'checkbox'
};

/**
 * Unified configuration that encompasses both node and panel configurations
 */
export interface UnifiedNodeConfig<T extends Record<string, unknown> = Record<string, unknown>> {
  // Node configuration properties
  label: string;
  icon: string;
  color: string;
  handles: NodeConfigItem['handles'];
  fields: FieldConfig[];
  defaults: Record<string, any>;
  
  // Panel configuration properties (optional overrides)
  panelLayout?: 'single' | 'twoColumn';
  panelFieldOverrides?: Partial<Record<keyof T, Partial<TypedPanelFieldConfig<T>>>>;
  panelFieldOrder?: Array<keyof T | 'labelPersonRow'>;
  panelCustomFields?: Array<TypedPanelFieldConfig<T>>;
}

/**
 * Derives a panel configuration from a unified node configuration
 */
export function derivePanelConfig<T extends Record<string, unknown>>(
  config: UnifiedNodeConfig<T>
): TypedPanelConfig<T> {
  const panelFields: Array<TypedPanelFieldConfig<T>> = [];
  const customFieldsMap = new Map(
    (config.panelCustomFields || []).map(field => [field.type === 'labelPersonRow' ? 'labelPersonRow' : field.name || field.type, field])
  );
  
  // Convert node fields to panel fields
  for (const field of config.fields) {
    const panelFieldType = fieldTypeMapping[field.type];
    
    const panelField: TypedPanelFieldConfig<T> = {
      type: panelFieldType,
      name: field.name as keyof T & string,
      label: field.label,
      placeholder: field.placeholder,
      required: field.required,
      // Apply overrides if specified
      ...(config.panelFieldOverrides?.[field.name as keyof T] || {})
    };
    
    // Special handling for specific field types
    if (field.type === 'select' && field.options) {
      panelField.options = field.options;
    }
    
    if (field.type === 'textarea') {
      panelField.rows = (field as any).rows || 4;
    }
    
    if (field.type === 'number') {
      if (field.min !== undefined) panelField.min = field.min;
      if (field.max !== undefined) panelField.max = field.max;
    }
    
    panelFields.push(panelField);
  }
  
  // Apply field ordering if specified
  const orderedFields = config.panelFieldOrder 
    ? orderFields(panelFields, config.panelFieldOrder, customFieldsMap)
    : panelFields;
  
  // Determine layout
  const layout = config.panelLayout || (orderedFields.length > 3 ? 'twoColumn' : 'single');
  
  if (layout === 'twoColumn') {
    // For personJob, we need specific column distribution
    if (config.panelFieldOrder) {
      const leftColumnFields: Array<TypedPanelFieldConfig<T>> = [];
      const rightColumnFields: Array<TypedPanelFieldConfig<T>> = [];
      
      // Split based on the original panel config layout
      const leftFieldNames = ['labelPersonRow', 'contextCleaningRule', 'maxIteration'];
      const rightFieldNames = ['defaultPrompt', 'firstOnlyPrompt'];
      
      for (const field of orderedFields) {
        const fieldKey = field.name || field.type;
        if (leftFieldNames.includes(fieldKey)) {
          leftColumnFields.push(field);
        } else if (rightFieldNames.includes(fieldKey)) {
          rightColumnFields.push(field);
        }
      }
      
      return {
        layout: 'twoColumn',
        leftColumn: leftColumnFields,
        rightColumn: rightColumnFields
      };
    } else {
      // Default split
      const midpoint = Math.ceil(orderedFields.length / 2);
      return {
        layout: 'twoColumn',
        leftColumn: orderedFields.slice(0, midpoint),
        rightColumn: orderedFields.slice(midpoint)
      };
    }
  }
  
  return {
    layout: 'single',
    fields: orderedFields
  };
}

/**
 * Orders fields according to specified order
 */
function orderFields<T extends Record<string, unknown>>(
  fields: Array<TypedPanelFieldConfig<T>>,
  order: Array<keyof T | string>,
  customFieldsMap?: Map<string, TypedPanelFieldConfig<T>>
): Array<TypedPanelFieldConfig<T>> {
  const fieldMap = new Map(
    fields.map(field => [field.name || field.type, field])
  );
  
  const orderedFields: Array<TypedPanelFieldConfig<T>> = [];
  
  for (const key of order) {
    const field = fieldMap.get(key as string);
    if (field) {
      orderedFields.push(field);
      fieldMap.delete(key as string);
    } else if (customFieldsMap?.has(key as string)) {
      // Add custom field from map
      orderedFields.push(customFieldsMap.get(key as string)!);
    } else if (key === 'labelPersonRow') {
      // Special case for labelPersonRow if not in custom fields
      orderedFields.push({
        type: 'labelPersonRow',
        labelPlaceholder: 'Person Job'
      } as TypedPanelFieldConfig<T>);
    }
  }
  
  // Add any remaining fields not in the order
  orderedFields.push(...fieldMap.values());
  
  return orderedFields;
}

/**
 * Creates a unified node configuration
 */
export function createUnifiedConfig<T extends Record<string, unknown>>(
  config: UnifiedNodeConfig<T>
): UnifiedNodeConfig<T> {
  return config;
}