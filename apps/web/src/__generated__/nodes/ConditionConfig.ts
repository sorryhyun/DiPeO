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
      { label: 'default', displayLabel: '', position: 'left' },
    ],
    output: [
      { label: 'condtrue', displayLabel: 'True', position: 'right' },
      { label: 'condfalse', displayLabel: 'False', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: conditionFields,
};

export default conditionConfig;