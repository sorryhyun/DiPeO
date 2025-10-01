// Auto-generated node configuration for person_job
import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
import { NodeType, HandleLabel, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { personJobFields } from '../fields/PersonJobFields';

export const personJobConfig: UnifiedNodeConfig = {
  label: 'Person Job',
  icon: '🤖',
  color: '#2196F3',
  nodeType: NodeType.PERSON_JOB,
  category: 'ai',
  handles: {
    input: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'left' },
      { label: HandleLabel.FIRST, displayLabel: '', position: 'left' },
    ],
    output: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
    first_only_prompt: '',
    max_iteration: 100,
    batch: false,
    batch_input_key: 'items',
    batch_parallel: true,
    max_concurrent: 10,
  },
  customFields: personJobFields,
  primaryDisplayField: 'person',
};

export default personJobConfig;
