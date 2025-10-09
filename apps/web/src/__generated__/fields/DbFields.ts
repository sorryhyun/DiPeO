// Generated field configuration for db
import type { UnifiedFieldDefinition } from '@/infrastructure/config/unifiedConfig';

export const dbFields: UnifiedFieldDefinition[] = [
  {
    name: 'file',
    type: 'text',
    label: '"File"',
    required: false,
    description: '"File path or array of file paths"',
  },
  {
    name: 'keys',
    type: 'password',
    label: '"Keys"',
    required: false,
    placeholder: '"e.g., user.profile.name or key1,key2"',
    description: '"Single key or list of dot-separated keys to target within the JSON payload"',
  },
  {
    name: 'lines',
    type: 'text',
    label: '"Lines"',
    required: false,
    placeholder: '"e.g., 1:120 or 5,10:20"',
    description: '"Line selection or ranges to read (e.g., 1:120 or [\'10:20\'])"',
  },
];
