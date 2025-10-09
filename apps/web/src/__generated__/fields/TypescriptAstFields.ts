// Generated field configuration for typescript_ast
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const typescriptAstFields: UnifiedFieldDefinition[] = [
  {
    name: 'source',
    type: 'text',
    label: '"Source"',
    required: false,
    description: '"TypeScript source code to parse"',
    language: 'typescript',
    adjustable: true,
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
    name: 'parse_mode',
    type: 'text',
    label: '"Parse mode"',
    required: false,
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
    name: 'output_format',
    type: 'text',
    label: '"Output format"',
    required: false,
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
    name: 'batch_input_key',
    type: 'password',
    label: '"Batch input key"',
    required: false,
    description: '"Key to extract batch items from input"',
  },
];
