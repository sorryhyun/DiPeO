







// Auto-generated node configuration for person_batch_job
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/domain-models';
import { personBatchJobFields } from '../fields/PersonBatchJobFields';

export const personBatchJobConfig: UnifiedNodeConfig = {
  label: 'Person Batch Job',
  icon: '📦',
  color: '#8b5cf6',
  nodeType: NodeType.PERSON_BATCH_JOB,
  category: 'ai',
  handles: {
    input: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'left' },
    ],
    output: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: personBatchJobFields,
  primaryDisplayField: 'batch_key',
};

export default personBatchJobConfig;