// Generated field configuration for typescript_ast
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const typescriptAstFields: UnifiedFieldDefinition[] = [
  {
    name: 'source',
    type: 'text',
    label: '"Source"',
    required: false,
    description: '"TypeScript source code to parse"',
    language: 'SupportedLanguage.TYPESCRIPT',
  },
  {
    name: 'extractPatterns',
    type: 'textarea',
    label: '"Extractpatterns"',
    required: false,
    defaultValue: ["interface", "type", "enum"],
    description: '"Patterns to extract from the AST"',
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'includeJSDoc',
    type: 'checkbox',
    label: '"Includejsdoc"',
    required: false,
    defaultValue: false,
    description: '"Include JSDoc comments in the extracted data"',
  },
  {
    name: 'parseMode',
    type: 'text',
    label: '"Parsemode"',
    required: false,
    defaultValue: "module",
    description: '"TypeScript parsing mode"',
    options: [
      { value: '"module"', label: '"Module"' },
      { value: '"script"', label: '"Script"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'transformEnums',
    type: 'checkbox',
    label: '"Transformenums"',
    required: false,
    defaultValue: false,
    description: '"Transform enum definitions to a simpler format"',
  },
  {
    name: 'flattenOutput',
    type: 'checkbox',
    label: '"Flattenoutput"',
    required: false,
    defaultValue: false,
    description: '"Flatten the output structure for easier consumption"',
  },
  {
    name: 'outputFormat',
    type: 'text',
    label: '"Outputformat"',
    required: false,
    defaultValue: "standard",
    description: '"Output format for the parsed data"',
    options: [
      { value: '"standard"', label: '"Standard"' },
      { value: '"for_codegen"', label: '"For Code Generation"' },
      { value: '"for_analysis"', label: '"For Analysis"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'batch',
    type: 'checkbox',
    label: '"Batch"',
    required: false,
    defaultValue: false,
    description: '"Enable batch processing mode"',
  },
  {
    name: 'batchInputKey',
    type: 'password',
    label: '"Batchinputkey"',
    required: false,
    defaultValue: "sources",
    description: '"Key to extract batch items from input"',
  },
];
