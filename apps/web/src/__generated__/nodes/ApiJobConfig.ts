







// Auto-generated node configuration for api_job
import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { apiJobFields } from '../fields/ApiJobFields';

export const apiJobConfig: UnifiedNodeConfig = {
  label: 'API Job',
  icon: '🌐',
  color: '#00BCD4',
  nodeType: NodeType.API_JOB,
  category: 'integration',
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
  customFields: apiJobFields,
  primaryDisplayField: 'method',
};

export default apiJobConfig;