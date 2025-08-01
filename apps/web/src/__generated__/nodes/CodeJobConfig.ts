







// Auto-generated node configuration for code_job
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { codeJobFields } from '../fields/CodeJobFields';

export const codeJobConfig: UnifiedNodeConfig = {
  label: 'Code Job',
  icon: '💻',
  color: '#9C27B0',
  nodeType: 'code_job',
  category: 'compute',
  handles: {
    input: [
      { label: 'default', displayLabel: '', position: 'left' },
    ],
    output: [
      { label: 'default', displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: codeJobFields,
  primaryDisplayField: 'language',
};

export default codeJobConfig;