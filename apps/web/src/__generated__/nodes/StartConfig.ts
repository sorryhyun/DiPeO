







// Auto-generated node configuration for start
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { startFields } from '../fields/StartFields';

export const startConfig: UnifiedNodeConfig = {
  label: 'Start Node',
  icon: '🚀',
  color: '#4CAF50',
  nodeType: 'start',
  category: 'control',
  handles: {
    output: [
      { label: 'default', displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
    trigger_mode: 'none',
  },
  customFields: startFields,
};

export default startConfig;