// Generated field configuration for integrated_api
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const integratedApiFields: UnifiedFieldDefinition[] = [
  {
    name: 'provider',
    type: 'text',
    label: '"Provider"',
    required: true,
    description: '"API provider to connect to"',
  },
  {
    name: 'operation',
    type: 'text',
    label: '"Operation"',
    required: true,
    placeholder: '"Select an operation"',
    description: '"Operation to perform (provider-specific)"',
  },
];
