// Auto-generated node configuration for hook
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { hookFields } from '../fields/HookFields';

export const hookConfig: UnifiedNodeConfig = {
  label: 'Hook',
  icon: '🪝',
  color: '#9333ea',
  nodeType: 'hook',
  category: 'control',
  handles: {
    input: [
      { id: 'data', label: '', position: 'left' },
    ],
    output: [
      { id: 'result', label: '', position: 'right' },
      { id: 'result', label: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: hookFields,
};

export default hookConfig;