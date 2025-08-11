







// Auto-generated node configuration for user_response
import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { userResponseFields } from '../fields/UserResponseFields';

export const userResponseConfig: UnifiedNodeConfig = {
  label: 'User Response',
  icon: '💬',
  color: '#E91E63',
  nodeType: NodeType.USER_RESPONSE,
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
    timeout: 300,
  },
  customFields: userResponseFields,
  primaryDisplayField: 'prompt',
};

export default userResponseConfig;