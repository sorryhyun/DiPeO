export const FIELD_TYPES = {
  TEXT: 'text',
  NUMBER: 'number',
  BOOLEAN: 'checkbox',
  SELECT: 'select',
  TEXTAREA: 'textarea',
  PERSON_SELECT: 'personSelect',
  VARIABLE_TEXTAREA: 'variableTextArea',
  MAX_ITERATION: 'maxIteration',
  LABEL_PERSON_ROW: 'labelPersonRow',
  ROW: 'row',
  CUSTOM: 'custom'
} as const;

export type FieldType = typeof FIELD_TYPES[keyof typeof FIELD_TYPES];

export interface ValidationResult {
  isValid: boolean;
  error?: string;
  warning?: string;
  fieldErrors?: Record<string, string>;
}

export type FieldValidator<T = unknown> = (
  value: unknown,
  formData: T
) => ValidationResult | { isValid: boolean; error?: string };

export type OptionsConfig<T = unknown> = 
  | Array<{ value: string; label: string }>
  | (() => Promise<Array<{ value: string; label: string }>>)
  | ((formData: T) => Promise<Array<{ value: string; label: string }>>);

export interface ConditionalConfig<T = unknown> {
  field: keyof T & string;
  values: unknown[];
  operator?: 'equals' | 'notEquals' | 'includes';
}

export interface BasePanelFieldConfig {
  type: FieldType;
  label?: string;
  placeholder?: string;
  required?: boolean;
  className?: string;
  rows?: number;
  min?: number;
  max?: number;
  labelPlaceholder?: string;
  personPlaceholder?: string;
  showPromptFileButton?: boolean;
}

export interface TypedPanelFieldConfig<T = unknown> extends BasePanelFieldConfig {
  name?: keyof T & string;
  disabled?: boolean | ((formData: T) => boolean);
  options?: OptionsConfig<T>;
  dependsOn?: Array<keyof T & string>;
  conditional?: ConditionalConfig<T>;
  fields?: Array<TypedPanelFieldConfig<T>>;
  validate?: FieldValidator<T>;
  column?: 1 | 2;
}

export interface PanelLayoutConfig<T = unknown> {
  layout: 'single' | 'twoColumn';
  fields?: Array<TypedPanelFieldConfig<T>>;
  leftColumn?: Array<TypedPanelFieldConfig<T>>;
  rightColumn?: Array<TypedPanelFieldConfig<T>>;
  validate?: (formData: T) => ValidationResult;
}

export type PanelFormData<T extends Record<string, unknown>> = Partial<T> & {
  [key: string]: unknown;
};

export type FieldChangeHandler<T = unknown> = (
  name: keyof T & string,
  value: unknown
) => void;

export interface PanelFormProps<T extends Record<string, unknown>> {
  data: PanelFormData<T>;
  config: PanelLayoutConfig<T>;
  onChange: FieldChangeHandler<T>;
  onValidate?: (result: ValidationResult) => void;
  className?: string;
}

export const DOMAIN_TO_UI_FIELD_TYPE: Record<string, FieldType> = {
  'string': FIELD_TYPES.TEXT,
  'number': FIELD_TYPES.NUMBER,
  'boolean': FIELD_TYPES.BOOLEAN,
  'select': FIELD_TYPES.SELECT,
  'textarea': FIELD_TYPES.VARIABLE_TEXTAREA,
  'person': FIELD_TYPES.PERSON_SELECT,
};

export function createPanelFormData<T extends Record<string, unknown>>(
  data: T
): PanelFormData<T> {
  return data as PanelFormData<T>;
}

export class FieldConfigBuilder<T extends Record<string, unknown> = Record<string, unknown>> {
  private config: TypedPanelFieldConfig<T>;

  constructor(type: FieldType, name?: keyof T & string) {
    this.config = { type, name };
  }

  label(label: string): this {
    this.config.label = label;
    return this;
  }

  placeholder(placeholder: string): this {
    this.config.placeholder = placeholder;
    return this;
  }

  required(required = true): this {
    this.config.required = required;
    return this;
  }

  disabled(disabled: boolean | ((formData: T) => boolean)): this {
    this.config.disabled = disabled;
    return this;
  }

  options(options: OptionsConfig<T>): this {
    this.config.options = options;
    return this;
  }

  dependsOn(...fields: Array<keyof T & string>): this {
    this.config.dependsOn = fields;
    return this;
  }

  conditional(field: keyof T & string, values: unknown[], operator?: ConditionalConfig<T>['operator']): this {
    this.config.conditional = { field, values, operator };
    return this;
  }

  validate(validator: FieldValidator<T>): this {
    this.config.validate = validator;
    return this;
  }

  rows(rows: number): this {
    this.config.rows = rows;
    return this;
  }

  min(min: number): this {
    this.config.min = min;
    return this;
  }

  max(max: number): this {
    this.config.max = max;
    return this;
  }

  column(column: 1 | 2): this {
    this.config.column = column;
    return this;
  }

  showPromptFileButton(show = true): this {
    this.config.showPromptFileButton = show;
    return this;
  }

  build(): TypedPanelFieldConfig<T> {
    return { ...this.config };
  }
}

export function field<T extends Record<string, unknown> = Record<string, unknown>>(
  type: FieldType,
  name?: keyof T & string
): FieldConfigBuilder<T> {
  return new FieldConfigBuilder<T>(type, name);
}