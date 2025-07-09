import type { NodeConfigItem } from '@/features/diagram-editor/types/config';
import type { PanelLayoutConfig, TypedPanelFieldConfig, PanelFieldType, ConditionalConfig, OptionsConfig } from '@/features/diagram-editor/types/panel';
import { FIELD_TYPES, type FieldType, type FieldValidator } from '@/core/types/panel';
import type { NodeTypeKey } from '@/core/types/type-factories';


/**
 * Unified field definition that can be used across all contexts
 */
export interface UnifiedFieldDefinition<T = any> {
  // Core properties
  name: string;
  type: FieldType;
  label: string;
  
  // Common properties
  required?: boolean;
  placeholder?: string;
  defaultValue?: unknown;
  description?: string;
  
  // UI properties
  rows?: number;
  min?: number;
  max?: number;
  disabled?: boolean | ((formData: T) => boolean);
  column?: 1 | 2;
  className?: string;
  
  // Behavior
  options?: OptionsConfig<T>;
  dependsOn?: string[];
  conditional?: ConditionalConfig<T>;
  
  // Validation
  validate?: FieldValidator<T>;
  
  // Special properties for specific field types
  labelPlaceholder?: string; // for labelPersonRow
  personPlaceholder?: string; // for labelPersonRow
  multiline?: boolean; // for textarea
  showPromptFileButton?: boolean; // for variableTextArea
  
  // Nested fields for composite types
  fields?: UnifiedFieldDefinition<T>[];
}

export interface UnifiedNodeConfig<T extends Record<string, unknown> = Record<string, unknown>> {
  label: string;
  icon: string;
  color: string;
  handles: NodeConfigItem['handles'];
  nodeType: NodeTypeKey;
  defaults: Record<string, unknown>;
  
  // Panel configuration properties (optional overrides)
  panelLayout?: 'single' | 'twoColumn';
  panelFieldOverrides?: Partial<Record<keyof T, Partial<TypedPanelFieldConfig<T>>>>;
  panelFieldOrder?: Array<keyof T | 'labelPersonRow'>;
  panelCustomFields?: Array<TypedPanelFieldConfig<T>>;
  
  // Allow custom field definitions to override registry
  customFields?: UnifiedFieldDefinition<T>[];
}


/**
 * Convert unified field definition to panel field config format
 */
function convertToPanelFieldConfig<T>(field: UnifiedFieldDefinition<T>): TypedPanelFieldConfig<T> {
  return {
    type: field.type,
    name: field.name as keyof T & string,
    label: field.label,
    placeholder: field.placeholder,
    required: field.required,
    className: field.className,
    rows: field.rows,
    min: field.min,
    max: field.max,
    labelPlaceholder: field.labelPlaceholder,
    personPlaceholder: field.personPlaceholder,
    disabled: field.disabled,
    options: field.options,
    dependsOn: field.dependsOn as Array<keyof T & string> | undefined,
    conditional: field.conditional,
    fields: field.fields?.map(f => convertToPanelFieldConfig(f)),
    validate: field.validate,
    column: field.column
  };
}

export function derivePanelConfig<T extends Record<string, unknown>>(
  config: UnifiedNodeConfig<T>
): PanelLayoutConfig<T> {
  // Convert custom fields to panel field configs
  const panelFields: Array<TypedPanelFieldConfig<T>> = [];
  
  if (config.customFields) {
    for (const field of config.customFields) {
      const panelField = convertToPanelFieldConfig<T>(field);
      
      // Apply any field-specific overrides
      if (config.panelFieldOverrides?.[field.name as keyof T]) {
        Object.assign(panelField, config.panelFieldOverrides[field.name as keyof T]);
      }
      
      panelFields.push(panelField);
    }
  }
  
  const customFieldsMap = new Map(
    (config.panelCustomFields || []).map(field => [field.type === FIELD_TYPES.LABEL_PERSON_ROW ? FIELD_TYPES.LABEL_PERSON_ROW : field.name || field.type, field])
  );

  
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