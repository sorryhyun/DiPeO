// Auto-generated node configuration for condition
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { conditionFields } from '../fields/ConditionFields';

export const conditionConfig: UnifiedNodeConfig = {
  label: 'Condition',
  icon: '🔀',
  color: '#FF9800',
  nodeType: 'condition',
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
  customFields: conditionFields,
};

export default conditionConfig;