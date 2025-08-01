







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
      { label: 'default', displayLabel: '', position: 'left' },
      { label: 'first', displayLabel: 'First', position: 'left' },
    ],
    output: [
      { label: 'default', displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
    max_iteration: 1,
    memory_profile: 'FOCUSED',
    tools: 'none',
  },
  customFields: personJobFields,
  primaryDisplayField: 'person',
};

export default personJobConfig;