// Generated field configuration for ir_builder
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const irBuilderFields: UnifiedFieldDefinition[] = [
  {
    name: 'builder_type',
    type: 'text',
    label: '"Builder type"',
    required: true,
    description: '"Type of IR builder to use"',
    options: [
      { value: '"backend"', label: '"Backend"' },
      { value: '"frontend"', label: '"Frontend"' },
      { value: '"strawberry"', label: '"Strawberry (GraphQL)"' },
      { value: '"custom"', label: '"Custom"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'source_type',
    type: 'text',
    label: '"Source type"',
    required: false,
    description: '"Type of source data"',
    options: [
      { value: '"ast"', label: '"AST"' },
      { value: '"schema"', label: '"Schema"' },
      { value: '"config"', label: '"Config"' },
      { value: '"auto"', label: '"Auto-detect"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'config_path',
    type: 'text',
    label: '"Config path"',
    required: false,
    placeholder: '"projects/codegen/config/"',
    description: '"Path to configuration directory"',
  },
  {
    name: 'output_format',
    type: 'text',
    label: '"Output format"',
    required: false,
    description: '"Output format for IR"',
    options: [
      { value: '"json"', label: '"JSON"' },
      { value: '"yaml"', label: '"YAML"' },
      { value: '"python"', label: '"Python"' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'cache_enabled',
    type: 'checkbox',
    label: '"Cache enabled"',
    required: false,
    description: '"Enable IR caching"',
  },
  {
    name: 'validate_output',
    type: 'text',
    label: '"Validate output"',
    required: false,
    description: '"Validate IR structure before output"',
  },
];
