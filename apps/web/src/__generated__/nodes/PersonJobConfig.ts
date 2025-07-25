// Auto-generated node configuration for person_job
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { personJobFields } from '../fields/PersonJobFields';

export const personJobConfig: UnifiedNodeConfig = {
  label: 'Person Job',
  icon: '🤖',
  color: '#2196F3',
  nodeType: 'person_job',
  category: 'ai',
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
  customFields: personJobFields,
};

export default personJobConfig;