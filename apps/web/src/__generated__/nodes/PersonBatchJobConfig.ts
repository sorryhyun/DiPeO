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
      { label: 'default', displayLabel: '', position: 'left' },
    ],
    output: [
      { label: 'default', displayLabel: 'Default', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: personBatchJobFields,
  primaryDisplayField: 'batch_size',
};

export default personBatchJobConfig;