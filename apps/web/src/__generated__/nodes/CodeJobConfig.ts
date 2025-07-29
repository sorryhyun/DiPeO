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
      { id: 'data', label: '', position: 'left' },
    ],
    output: [
      { id: 'result', label: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: codeJobFields,
};

export default codeJobConfig;