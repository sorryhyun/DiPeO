// Auto-generated node configuration for db
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { dbFields } from '../fields/DbFields';

export const dbConfig: UnifiedNodeConfig = {
  label: 'Database',
  icon: '🗄️',
  color: '#795548',
  nodeType: 'db',
  category: 'data',
  handles: {
    input: [
      { label: 'default', displayLabel: '', position: 'left' },
    ],
    output: [
      { label: 'default', displayLabel: 'Default', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: dbFields,
};

export default dbConfig;