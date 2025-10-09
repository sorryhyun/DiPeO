/**
 * Reusable field presets for common entities in node specifications
 *
 * These presets reduce duplication and ensure consistency across node specs.
 * Each preset is a factory function that returns a FieldSpecification with
 * optional customization through parameters.
 *
 * Usage example:
 * ```ts
 * import { personField, promptWithFileField, timeoutField } from '../core/field-presets.js';
 *
 * const myNodeSpec: NodeSpecification = {
 *   fields: [
 *     personField(),
 *     promptWithFileField({ name: 'custom_prompt' }),
 *     timeoutField({ defaultValue: 60 }),
 *     // ... other fields
 *   ]
 * };
 * ```
 */

import type { FieldSpecification } from '../node-specification.js';
import { SupportedLanguage } from './enums/node-specific.js';
import { validatedNumberField, validatedEnumField } from './validation-utils.js';

/**
 * Person Selection Field
 * Used for selecting an AI person/agent
 */
export function personField(overrides?: Partial<FieldSpecification>): FieldSpecification {
  return {
    name: "person",
    type: "PersonID",
    required: false,
    description: "AI person to use for this task",
    uiConfig: {
      inputType: "personSelect"
    },
    ...overrides
  };
}

/**
 * Prompt Field with File Support
 * Combines a textarea for inline prompts with optional file loading
 * Returns an array of two fields: [promptField, promptFileField]
 */
export function promptWithFileField(options?: {
  name?: string;
  fileFieldName?: string;
  description?: string;
  placeholder?: string;
  rows?: number;
  column?: 1 | 2;
  required?: boolean;
  conditionalConfig?: FieldSpecification['conditional'];
}): FieldSpecification[] {
  const {
    name = 'default_prompt',
    fileFieldName = 'prompt_file',
    description = 'Prompt template',
    placeholder = 'Enter prompt template...',
    rows = 10,
    column = 2,
    required = false,
    conditionalConfig
  } = options || {};

  return [
    {
      name,
      type: "string",
      required,
      description,
      ...(conditionalConfig && { conditional: conditionalConfig }),
      uiConfig: {
        inputType: "textarea",
        placeholder,
        column,
        rows,
        adjustable: true,
        showPromptFileButton: true
      }
    },
    {
      name: fileFieldName,
      type: "string",
      required: false,
      description: `Path to prompt file in /files/prompts/`,
      ...(conditionalConfig && { conditional: conditionalConfig }),
      uiConfig: {
        inputType: "text",
        placeholder: "example.txt",
        column,
        hidden: true
      }
    }
  ];
}

/**
 * Memory Control Fields
 * Returns an array of fields for controlling AI memory/context
 */
export function memoryControlFields(options?: {
  includeIgnorePerson?: boolean;
  defaultMemorizeTo?: string;
  maxAtMost?: number;
}): FieldSpecification[] {
  const {
    includeIgnorePerson = false,
    defaultMemorizeTo,
    maxAtMost = 500
  } = options || {};

  const fields: FieldSpecification[] = [
    textField({
      name: "memorize_to",
      description: "Criteria used to select helpful messages for this task. Empty = memorize all. Special: 'GOLDFISH' for goldfish mode. Comma-separated for multiple criteria.",
      placeholder: "e.g., requirements, acceptance criteria, API keys",
      column: 2,
      ...(defaultMemorizeTo && { defaultValue: defaultMemorizeTo })
    }),
    validatedNumberField({
      name: "at_most",
      description: "Select at most N messages to keep (system messages may be preserved in addition).",
      min: 1,
      max: maxAtMost,
      column: 1
    })
  ];

  if (includeIgnorePerson) {
    fields.push(textField({
      name: "ignore_person",
      description: "Comma-separated list of person IDs whose messages should be excluded from memory selection.",
      placeholder: "e.g., assistant, user2",
      column: 2
    }));
  }

  return fields;
}

/**
 * Batch Execution Fields
 * Returns an array of fields for batch processing configuration
 */
export function batchExecutionFields(options?: {
  defaultBatchInputKey?: string;
  defaultMaxConcurrent?: number;
  maxConcurrentLimit?: number;
}): FieldSpecification[] {
  const {
    defaultBatchInputKey = 'items',
    defaultMaxConcurrent = 10,
    maxConcurrentLimit = 100
  } = options || {};

  return [
    booleanField({
      name: "batch",
      description: "Enable batch mode for processing multiple items",
      defaultValue: false
    }),
    textField({
      name: "batch_input_key",
      description: "Key containing the array to iterate over in batch mode",
      defaultValue: defaultBatchInputKey,
      placeholder: defaultBatchInputKey
    }),
    booleanField({
      name: "batch_parallel",
      description: "Execute batch items in parallel",
      defaultValue: true
    }),
    validatedNumberField({
      name: "max_concurrent",
      description: "Maximum concurrent executions in batch mode",
      defaultValue: defaultMaxConcurrent,
      min: 1,
      max: maxConcurrentLimit
    })
  ];
}

/**
 * Timeout Field
 * Common timeout configuration for operations
 * Uses validatedNumberField to eliminate validation/uiConfig duplication
 */
export function timeoutField(options?: {
  name?: string;
  description?: string;
  defaultValue?: number;
  min?: number;
  max?: number;
  required?: boolean;
}): FieldSpecification {
  const {
    name = 'timeout',
    description = 'Operation timeout in seconds',
    defaultValue,
    min = 0,
    max = 3600,
    required = false
  } = options || {};

  return validatedNumberField({
    name,
    description,
    min,
    max,
    defaultValue,
    required
  });
}

/**
 * Object/Code Editor Field
 * Common field for editing structured data or code
 */
export function objectField(options: {
  name: string;
  description: string;
  required?: boolean;
  language?: SupportedLanguage;
  collapsible?: boolean;
}): FieldSpecification {
  const {
    name,
    description,
    required = false,
    language,
    collapsible = true
  } = options;

  return {
    name,
    type: "object",
    required,
    description,
    uiConfig: {
      inputType: language ? "code" : "code",
      ...(language && { language }),
      collapsible
    }
  };
}

/**
 * File Path Field
 * Common field for file path input
 */
export function filePathField(options: {
  name?: string;
  description?: string;
  placeholder?: string;
  required?: boolean;
}): FieldSpecification {
  const {
    name = 'file_path',
    description = 'Path to file',
    placeholder = '/path/to/file',
    required = false
  } = options || {};

  return {
    name,
    type: "string",
    required,
    description,
    uiConfig: {
      inputType: "text",
      placeholder
    }
  };
}

/**
 * Content Field
 * Common field for inline content (alternative to file path)
 */
export function contentField(options: {
  name?: string;
  description?: string;
  placeholder?: string;
  rows?: number;
  inputType?: 'textarea' | 'code';
  language?: SupportedLanguage;
  required?: boolean;
}): FieldSpecification {
  const {
    name = 'content',
    description = 'Inline content',
    placeholder = 'Enter content...',
    rows = 10,
    inputType = 'textarea',
    language,
    required = false
  } = options || {};

  return {
    name,
    type: "string",
    required,
    description,
    uiConfig: {
      inputType,
      placeholder,
      rows,
      adjustable: true,
      ...(language && { language })
    }
  };
}

/**
 * File or Content Pair
 * Returns an array of two fields: one for file path, one for inline content
 * Common pattern when users can either provide a file or inline content
 */
export function fileOrContentFields(options?: {
  fileFieldName?: string;
  contentFieldName?: string;
  fileDescription?: string;
  contentDescription?: string;
  contentPlaceholder?: string;
  contentInputType?: 'textarea' | 'code';
  language?: SupportedLanguage;
  rows?: number;
}): FieldSpecification[] {
  const {
    fileFieldName = 'file_path',
    contentFieldName = 'content',
    fileDescription = 'Path to file',
    contentDescription = 'Inline content (alternative to file_path)',
    contentPlaceholder = 'Enter content...',
    contentInputType = 'textarea',
    language,
    rows = 10
  } = options || {};

  return [
    filePathField({
      name: fileFieldName,
      description: fileDescription,
      required: false
    }),
    contentField({
      name: contentFieldName,
      description: contentDescription,
      placeholder: contentPlaceholder,
      inputType: contentInputType,
      language,
      rows,
      required: false
    })
  ];
}

/**
 * Boolean Checkbox Field
 * Common field for boolean flags
 */
export function booleanField(options: {
  name: string;
  description: string;
  defaultValue?: boolean;
  required?: boolean;
}): FieldSpecification {
  const {
    name,
    description,
    defaultValue = false,
    required = false
  } = options;

  return {
    name,
    type: "boolean",
    required,
    defaultValue,
    description,
    uiConfig: {
      inputType: "checkbox"
    }
  };
}

/**
 * Number Field with Validation
 * Common field for numeric input with min/max constraints
 * Uses validatedNumberField to eliminate validation/uiConfig duplication
 */
export function numberField(options: {
  name: string;
  description: string;
  defaultValue?: number;
  min?: number;
  max?: number;
  required?: boolean;
  placeholder?: string;
  column?: 1 | 2;
}): FieldSpecification {
  return validatedNumberField(options);
}

/**
 * Text Field
 * Common field for text input
 */
export function textField(options: {
  name: string;
  description: string;
  placeholder?: string;
  required?: boolean;
  defaultValue?: string;
  column?: 1 | 2;
}): FieldSpecification {
  const {
    name,
    description,
    placeholder,
    required = false,
    defaultValue,
    column
  } = options;

  return {
    name,
    type: "string",
    required,
    ...(defaultValue !== undefined && { defaultValue }),
    description,
    uiConfig: {
      inputType: "text",
      ...(placeholder && { placeholder }),
      ...(column && { column })
    }
  };
}

/**
 * Enum Select Field
 * Common field for enum selection with dropdown
 * Uses validatedEnumField to eliminate validation/uiConfig duplication
 */
export function enumSelectField<T extends string = string>(options: {
  name: string;
  description: string;
  options: Array<{ value: T; label: string }>;
  defaultValue?: T;
  required?: boolean;
  column?: 1 | 2;
}): FieldSpecification {
  return validatedEnumField(options);
}
