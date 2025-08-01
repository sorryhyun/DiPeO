







// Generated field configuration for typescript_ast
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const typescriptAstFields: UnifiedFieldDefinition[] = [
  {
    name: 'source',
    type: 'code',
    label: 'Source',
    required: true,
    description: 'TypeScript source code to parse',
    language: 'SupportedLanguage.TYPESCRIPT',
  },
  {
    name: 'extractPatterns',
    type: 'code',
    label: 'Extract Patterns',
    required: false,
    defaultValue: ["interface", "type", "enum"],
    description: 'Patterns to extract from the AST',
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'includeJSDoc',
    type: 'checkbox',
    label: 'Include Js Doc',
    required: false,
    defaultValue: false,
    description: 'Include JSDoc comments in the extracted data',
  },
  {
    name: 'parseMode',
    type: 'select',
    label: 'Parse Mode',
    required: false,
    defaultValue: "module",
    description: 'TypeScript parsing mode',
    options: [
      { value: 'module', label: 'Module' },
      { value: 'script', label: 'Script' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'transformEnums',
    type: 'checkbox',
    label: 'Transform Enums',
    required: false,
    defaultValue: false,
    description: 'Transform enum definitions to a simpler format',
  },
  {
    name: 'flattenOutput',
    type: 'checkbox',
    label: 'Flatten Output',
    required: false,
    defaultValue: false,
    description: 'Flatten the output structure for easier consumption',
  },
  {
    name: 'outputFormat',
    type: 'select',
    label: 'Output Format',
    required: false,
    defaultValue: "standard",
    description: 'Output format for the parsed data',
    options: [
      { value: 'standard', label: 'Standard' },
      { value: 'for_codegen', label: 'For Code Generation' },
      { value: 'for_analysis', label: 'For Analysis' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
];