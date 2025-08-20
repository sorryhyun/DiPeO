// Auto-generated node configuration for template_job
import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { templateJobFields } from '../fields/TemplateJobFields';

export const templateJobConfig: UnifiedNodeConfig = {
  label: 'Template Job',
  icon: '📝',
  color: '#3F51B5',
  nodeType: NodeType.TEMPLATE_JOB,
  category: 'codegen',
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
  customFields: templateJobFields,
  primaryDisplayField: 'engine',
};

export default templateJobConfig;