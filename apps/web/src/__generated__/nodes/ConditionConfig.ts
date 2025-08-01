







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
      { label: 'condtrue', displayLabel: 'Condtrue', position: 'right' },
      { label: 'condfalse', displayLabel: 'Condfalse', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: conditionFields,
  primaryDisplayField: 'condition_type',
};

export default conditionConfig;