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
      { id: 'input', label: '', position: 'left' },
    ],
    output: [
      { id: 'output', label: '', position: 'right' },
      { id: 'output', label: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: hookFields,
};

export default hookConfig;