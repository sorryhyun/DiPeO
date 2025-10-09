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
    name: 'extract_patterns',
    type: 'textarea',
    label: '"Extract patterns"',
    required: false,
    description: '"Patterns to extract from the AST"',
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'include_jsdoc',
    type: 'checkbox',
    label: '"Include jsdoc"',
    required: false,
    description: '"Include JSDoc comments in the extracted data"',
  },
  {
    name: 'parse_mode',
    type: 'text',
    label: '"Parse mode"',
    required: false,
    description: '"TypeScript parsing mode"',
    options: [
      { value: '"TypeScriptParseMode.MODULE"', label: '"Module"' },
      { value: '"TypeScriptParseMode.SCRIPT"', label: '"Script"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'transform_enums',
    type: 'checkbox',
    label: '"Transform enums"',
    required: false,
    description: '"Transform enum definitions to a simpler format"',
  },
  {
    name: 'flatten_output',
    type: 'checkbox',
    label: '"Flatten output"',
    required: false,
    description: '"Flatten the output structure for easier consumption"',
  },
  {
    name: 'output_format',
    type: 'text',
    label: '"Output format"',
    required: false,
    description: '"Output format for the parsed data"',
    options: [
      { value: '"TypeScriptOutputFormat.STANDARD"', label: '"Standard"' },
      { value: '"TypeScriptOutputFormat.FOR_CODEGEN"', label: '"For Code Generation"' },
      { value: '"TypeScriptOutputFormat.FOR_ANALYSIS"', label: '"For Analysis"' },
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
    description: '"Enable batch processing mode"',
  },
  {
    name: 'batch_input_key',
    type: 'password',
    label: '"Batch input key"',
    required: false,
    description: '"Key to extract batch items from input"',
  },
];
