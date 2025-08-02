







// Auto-generated node configuration for start
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/domain-models';
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
  },
  customFields: startFields,
};

export default startConfig;