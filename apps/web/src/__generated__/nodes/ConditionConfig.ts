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
      { id: 'data', label: '', position: 'left' },
    ],
    output: [
      { id: 'result', label: '', position: 'right' },
      { id: 'result', label: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: conditionFields,
};

export default conditionConfig;