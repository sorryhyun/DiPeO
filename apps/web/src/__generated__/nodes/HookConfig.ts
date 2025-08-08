







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
      { label: HandleLabel.SUCCESS, displayLabel: 'Success', position: 'right' },
      { label: HandleLabel.ERROR, displayLabel: 'Error', position: 'right' },
    ],
  },
  defaults: {
    hook_type: HookType.SHELL,
    timeout: 60,
    retry_count: 0,
  },
  customFields: hookFields,
  primaryDisplayField: 'hook_type',
};

export default hookConfig;