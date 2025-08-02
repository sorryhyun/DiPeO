







// Auto-generated node configuration for user_response
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/domain-models';
import { userResponseFields } from '../fields/UserResponseFields';

export const userResponseConfig: UnifiedNodeConfig = {
  label: 'User Response',
  icon: '💬',
  color: '#E91E63',
  nodeType: NodeType.USER_RESPONSE,
  category: 'interaction',
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
  customFields: userResponseFields,
  primaryDisplayField: 'response_type',
};

export default userResponseConfig;