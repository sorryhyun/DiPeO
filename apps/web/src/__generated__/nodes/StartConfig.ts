// Auto-generated node configuration for start
import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
import { NodeType, HandleLabel, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { startFields } from '../fields/StartFields';

export const startConfig: UnifiedNodeConfig = {
  label: 'Start Node',
  icon: '🚀',
  color: '#4CAF50',
  nodeType: NodeType.START,
  category: 'control',
  handles: {
    output: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
    trigger_mode: HookTriggerMode.NONE,
    custom_data: {},
    output_data_structure: {},
  },
  customFields: startFields,
};

export default startConfig;
