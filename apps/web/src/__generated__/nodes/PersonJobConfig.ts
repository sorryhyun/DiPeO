







// Auto-generated node configuration for person_job
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
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
      { label: HandleLabel.FIRST, displayLabel: 'First', position: 'left' },
    ],
    output: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
    max_iteration: 1,
    memory_profile: MemoryProfile.FOCUSED,
    tools: ToolSelection.NONE,
  },
  customFields: personJobFields,
  primaryDisplayField: 'person',
};

export default personJobConfig;