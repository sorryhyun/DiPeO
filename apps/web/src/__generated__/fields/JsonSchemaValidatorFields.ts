// Generated field configuration for json_schema_validator
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const jsonSchemaValidatorFields: UnifiedFieldDefinition[] = [
  {
    name: 'schema_path',
    type: 'text',
    label: 'Schema path',
    required: false,
    placeholder: '/path/to/file',
    description: 'Path to JSON schema file',
  },
  {
    name: 'schema',
    type: 'code',
    label: 'Schema',
    required: false,
    description: 'Inline JSON schema',
  },
  {
    name: 'data_path',
    type: 'text',
    label: 'Data path',
    required: false,
    placeholder: '/path/to/file',
    description: 'Data Path configuration',
  },
  {
    name: 'strict_mode',
    type: 'checkbox',
    label: 'Strict mode',
    required: false,
    description: 'Strict Mode configuration',
  },
  {
    name: 'error_on_extra',
    type: 'checkbox',
    label: 'Error on extra',
    required: false,
    description: 'Error On Extra configuration',
  },
];
