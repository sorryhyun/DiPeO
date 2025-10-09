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
      { value: '"IRBuilderTargetType.BACKEND"', label: '"Backend"' },
      { value: '"IRBuilderTargetType.FRONTEND"', label: '"Frontend"' },
      { value: '"IRBuilderTargetType.STRAWBERRY"', label: '"Strawberry (GraphQL)"' },
      { value: '"IRBuilderTargetType.CUSTOM"', label: '"Custom"' },
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
      { value: '"IRBuilderSourceType.AST"', label: '"AST"' },
      { value: '"IRBuilderSourceType.SCHEMA"', label: '"Schema"' },
      { value: '"IRBuilderSourceType.CONFIG"', label: '"Config"' },
      { value: '"IRBuilderSourceType.AUTO"', label: '"Auto-detect"' },
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
      { value: '"IRBuilderOutputFormat.JSON"', label: '"JSON"' },
      { value: '"IRBuilderOutputFormat.YAML"', label: '"YAML"' },
      { value: '"IRBuilderOutputFormat.PYTHON"', label: '"Python"' },
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
