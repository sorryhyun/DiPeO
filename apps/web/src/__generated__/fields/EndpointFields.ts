







// Generated field configuration for endpoint
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const endpointFields: UnifiedFieldDefinition[] = [
  {
    name: 'save_to_file',
    type: 'checkbox',
    label: 'Save To File',
    required: true,
    description: 'Save results to file',
  },
  {
    name: 'file_name',
    type: 'text',
    label: 'File Name',
    required: false,
    description: 'Output filename',
  },
];