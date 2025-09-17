// Generated field configuration for endpoint
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const endpointFields: UnifiedFieldDefinition[] = [
  {
    name: 'save_to_file',
    type: 'checkbox',
    label: '"Save to file"',
    required: true,
    description: '"Save results to file"',
  },
  {
    name: 'file_name',
    type: 'text',
    label: '"File name"',
    required: false,
    description: '"Output filename"',
  },
];
