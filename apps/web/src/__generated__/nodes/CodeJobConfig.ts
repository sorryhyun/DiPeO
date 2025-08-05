







// Auto-generated node configuration for code_job
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { codeJobFields } from '../fields/CodeJobFields';

export const codeJobConfig: UnifiedNodeConfig = {
  label: 'Code Job',
  icon: '💻',
  color: '#9C27B0',
  nodeType: NodeType.CODE_JOB,
  category: 'compute',
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
  customFields: codeJobFields,
  primaryDisplayField: 'language',
};

export default codeJobConfig;