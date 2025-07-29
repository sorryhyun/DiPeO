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
      { id: 'data', label: '', position: 'left' },
    ],
    output: [
      { id: 'result', label: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: userResponseFields,
};

export default userResponseConfig;