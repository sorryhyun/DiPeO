// Auto-generated node configuration for person_batch_job
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { personBatchJobFields } from '../fields/PersonBatchJobFields';

export const personBatchJobConfig: UnifiedNodeConfig = {
  label: 'Person Batch Job',
  icon: '📦',
  color: '#8b5cf6',
  nodeType: 'person_batch_job',
  category: 'ai',
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
  customFields: personBatchJobFields,
};

export default personBatchJobConfig;