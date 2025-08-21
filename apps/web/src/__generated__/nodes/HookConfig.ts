// Auto-generated node configuration for hook
import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { hookFields } from '../fields/HookFields';

export const hookConfig: UnifiedNodeConfig = {
  label: 'Hook',
  icon: '🪝',
  color: '#9333ea',
  nodeType: NodeType.HOOK,
  category: 'compute',
  handles: {
    input: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'left' },
    ],
    output: [
      { label: HandleLabel.SUCCESS, displayLabel: '', position: 'right' },
      { label: HandleLabel.ERROR, displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: hookFields,
  primaryDisplayField: 'hook_type',
};

export default hookConfig;