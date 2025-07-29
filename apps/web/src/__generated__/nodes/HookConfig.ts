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
      { label: 'default', displayLabel: '', position: 'left' },
    ],
    output: [
      { label: 'success', displayLabel: 'Success', position: 'right' },
      { label: 'error', displayLabel: 'Error', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: hookFields,
};

export default hookConfig;