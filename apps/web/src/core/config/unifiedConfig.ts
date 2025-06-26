import type { NodeConfigItem, FieldConfig } from '@/features/diagram-editor/types';
import type { PanelLayoutConfig, TypedPanelFieldConfig } from '@/features/diagram-editor/types/panel';
import { FIELD_TYPES, type FieldType } from '@/core/types/panel';

const fieldTypeMapping: Record<FieldConfig['type'], FieldType> = {
  string: FIELD_TYPES.TEXT,
  number: FIELD_TYPES.TEXT, // Will add number validation
  select: FIELD_TYPES.SELECT,
  textarea: FIELD_TYPES.VARIABLE_TEXTAREA,
  person: FIELD_TYPES.PERSON_SELECT,
  boolean: FIELD_TYPES.BOOLEAN
};


export interface UnifiedNodeConfig<T extends Record<string, unknown> = Record<string, unknown>> {
  label: string;
  icon: string;
  color: string;
  handles: NodeConfigItem['handles'];
  fields: FieldConfig[];
  defaults: Record<string, unknown>;
  
  // Panel configuration properties (optional overrides)
  panelLayout?: 'single' | 'twoColumn';
  panelFieldOverrides?: Partial<Record<keyof T, Partial<TypedPanelFieldConfig<T>>>>;
  panelFieldOrder?: Array<keyof T | 'labelPersonRow'>;
  panelCustomFields?: Array<TypedPanelFieldConfig<T>>;
}


export function derivePanelConfig<T extends Record<string, unknown>>(
  config: UnifiedNodeConfig<T>
): PanelLayoutConfig<T> {

  const panelFields: Array<TypedPanelFieldConfig<T>> = [];
  const customFieldsMap = new Map(
    (config.panelCustomFields || []).map(field => [field.type === FIELD_TYPES.LABEL_PERSON_ROW ? FIELD_TYPES.LABEL_PERSON_ROW : field.name || field.type, field])
  );


  for (const field of config.fields) {
    const panelFieldType = fieldTypeMapping[field.type];
    
    const panelField: TypedPanelFieldConfig<T> = {
      type: panelFieldType as FieldType,
      name: field.name as keyof T & string,
      label: field.label,
      placeholder: field.placeholder,
      required: field.required,
      ...(config.panelFieldOverrides?.[field.name as keyof T] || {})
    };
    
    // Special handling for specific field types
    if (field.type === 'select' && field.options) {
      panelField.options = field.options;
    }
    
    if (field.type === 'textarea') {
      panelField.rows = (field as FieldConfig & { rows?: number }).rows || 4;
    }
    
    if (field.type === 'number') {
      if (field.min !== undefined) panelField.min = field.min;
      if (field.max !== undefined) panelField.max = field.max;
    }
    
    panelFields.push(panelField);
  }

  
  const orderedFields = config.panelFieldOrder 
    ? orderFields(panelFields, config.panelFieldOrder, customFieldsMap)
    : [...panelFields, ...(config.panelCustomFields || [])];
  
  // Determine layout
  const layout = config.panelLayout || (orderedFields.length > 3 ? 'twoColumn' : 'single');
  
  if (layout === 'twoColumn') {
    const leftColumnFields: Array<TypedPanelFieldConfig<T>> = [];
    const rightColumnFields: Array<TypedPanelFieldConfig<T>> = [];
    
    // First, group fields by explicit column assignment
    const fieldsWithColumn1: Array<TypedPanelFieldConfig<T>> = [];
    const fieldsWithColumn2: Array<TypedPanelFieldConfig<T>> = [];
    const fieldsWithoutColumn: Array<TypedPanelFieldConfig<T>> = [];
    
    for (const field of orderedFields) {
      if (field.column === 1) {
        fieldsWithColumn1.push(field);
      } else if (field.column === 2) {
        fieldsWithColumn2.push(field);
      } else {
        fieldsWithoutColumn.push(field);
      }
    }
    
    // Add explicitly assigned fields first
    leftColumnFields.push(...fieldsWithColumn1);
    rightColumnFields.push(...fieldsWithColumn2);
    
    // Handle fields without explicit column assignment
    if (fieldsWithoutColumn.length > 0) {
      if (config.panelFieldOrder) {
        // Legacy behavior for personJob
        const leftFieldNames = ['labelPersonRow', 'contextCleaningRule', 'maxIteration'];
        const rightFieldNames = ['defaultPrompt', 'firstOnlyPrompt'];
        
        for (const field of fieldsWithoutColumn) {
          const fieldKey = field.name || field.type;
          if (leftFieldNames.includes(fieldKey)) {
            leftColumnFields.push(field);
          } else if (rightFieldNames.includes(fieldKey)) {
            rightColumnFields.push(field);
          } else {
            // Default: add to left column
            leftColumnFields.push(field);
          }
        }
      } else {
        // Distribute remaining fields evenly
        const currentLeftCount = leftColumnFields.length;
        const currentRightCount = rightColumnFields.length;
        
        fieldsWithoutColumn.forEach((field, index) => {
          if (currentLeftCount + index <= currentRightCount + (fieldsWithoutColumn.length - index - 1)) {
            leftColumnFields.push(field);
          } else {
            rightColumnFields.push(field);
          }
        });
      }
    }
    
    return {
      layout: 'twoColumn',
      leftColumn: leftColumnFields,
      rightColumn: rightColumnFields
    };
  }
  
  const result = {
    layout: 'single' as const,
    fields: orderedFields
  };
  return result;
}

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
      const customField = customFieldsMap.get(key as string)!;
      orderedFields.push(customField);
    } else if (key === 'labelPersonRow') {
      // Special case for labelPersonRow if not in custom fields
      orderedFields.push({
        type: 'labelPersonRow',
        labelPlaceholder: 'Person Job'
      } as TypedPanelFieldConfig<T>);
    } else {
      console.log(`  Field not found for key: ${String(key)}`);
    }
  }
  
  // Add any remaining fields not in the order
  const remainingFields = Array.from(fieldMap.values());
  orderedFields.push(...remainingFields);

  return orderedFields;
}


export function createUnifiedConfig<T extends Record<string, unknown>>(
  config: UnifiedNodeConfig<T>
): UnifiedNodeConfig<T> {
  return config;
}