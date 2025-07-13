export interface ValidationError {
  field: string;
  message: string;
  code?: string;
}

export interface ValidationResult {
  valid: boolean;
  errors: ValidationError[];
}

export type FieldValidator<T = any> = (
  value: T,
  formData?: Record<string, any>
) => ValidationResult | Promise<ValidationResult>;

export interface FormState<T extends Record<string, any> = Record<string, any>> {
  data: T;
  errors: Record<string, ValidationError[]>;
  touched: Record<string, boolean>;
  dirty: Record<string, boolean>;
  isSubmitting: boolean;
  isValidating: boolean;
}

export interface FormConfig<T extends Record<string, any> = Record<string, any>> {
  initialValues: T;
  validators?: Record<string, FieldValidator>;
  validateOnChange?: boolean;
  validateOnBlur?: boolean;
  enableReinitialize?: boolean;
}

export interface FormFieldUpdate<T = any> {
  field: string;
  value: T;
  validate?: boolean;
  touch?: boolean;
}

export interface FormOperations<T extends Record<string, any> = Record<string, any>> {
  updateField: (update: FormFieldUpdate) => void;
  updateFields: (updates: Partial<T>) => void;
  setFieldError: (field: string, error: ValidationError | null) => void;
  setFieldTouched: (field: string, touched?: boolean) => void;
  validateField: (field: string) => Promise<ValidationResult>;
  validateForm: () => Promise<ValidationResult>;
  reset: (values?: Partial<T>) => void;
  submit: () => Promise<void>;
}

export type FormAutoSaveConfig = {
  enabled: boolean;
  delay?: number;
  onSave: (data: any) => Promise<void>;
  fields?: string[];
};

export interface AsyncFieldOptions {
  queryKey: string[];
  queryFn: () => Promise<any[]>;
  dependencies?: string[];
  enabled?: boolean;
}