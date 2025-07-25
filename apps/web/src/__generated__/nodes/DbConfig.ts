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
      { id: 'input', label: '', position: 'left' },
    ],
    output: [
      { id: 'output', label: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: dbFields,
};

export default dbConfig;