// Generated field configuration for json_schema_validator
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const jsonSchemaValidatorFields: UnifiedFieldDefinition[] = [
  {
    name: 'json_schema',
    type: 'textarea',
    label: '"Json schema"',
    required: false,
    description: '"Inline JSON schema"',
  },
  {
    name: 'data_path',
    type: 'text',
    label: '"Data path"',
    required: false,
    placeholder: '"/path/to/file"',
    description: '"Data Path configuration"',
  },
];
