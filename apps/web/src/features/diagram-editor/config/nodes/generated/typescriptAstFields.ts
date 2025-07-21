// Generated field configuration for typescript_ast
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const typescriptAstFields: UnifiedFieldDefinition[] = [
  {
    name: 'source',
    type: 'text',
    label: 'Source',
    required: true,
    description: 'TypeScript source code to parse',
  },
  {
    name: 'extractPatterns',
    type: 'text',
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
    label: 'Include Jsdoc',
    required: false,
    description: 'Include JSDoc comments in the extracted data',
  },
  {
    name: 'parseMode',
    type: 'select',
    label: 'Parse Mode',
    required: false,
    defaultValue: 'module',
    description: 'TypeScript parsing mode',
    options: [
      { value: 'module', label: 'Module' },
      { value: 'script', label: 'Script' },
    ],
  },
];