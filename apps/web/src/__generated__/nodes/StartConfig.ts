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

    input: [

      { id: 'input', label: '', position: 'left' },

    ],


    output: [

      { id: 'output', label: '', position: 'right' },

    ],

  },
  defaults: {

  },
  customFields: startFields,
};

export default startConfig;