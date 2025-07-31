// Auto-generated node configuration for user_response
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { userResponseFields } from '../fields/UserResponseFields';

export const userResponseConfig: UnifiedNodeConfig = {
  label: 'User Response',
  icon: '💬',
  color: '#E91E63',
  nodeType: 'user_response',
  category: 'interaction',
  handles: {
    input: [
      { label: 'default', displayLabel: '', position: 'left' },
    ],
    output: [
      { label: 'default', displayLabel: 'Default', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: userResponseFields,
  primaryDisplayField: 'response_type',
};

export default userResponseConfig;