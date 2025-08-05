







// Auto-generated node configuration for condition
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { conditionFields } from '../fields/ConditionFields';

export const conditionConfig: UnifiedNodeConfig = {
  label: 'Condition',
  icon: '🔀',
  color: '#FF9800',
  nodeType: NodeType.CONDITION,
  category: 'control',
  handles: {
    input: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'left' },
    ],
    output: [
      { label: HandleLabel.CONDTRUE, displayLabel: 'Condtrue', position: 'right' },
      { label: HandleLabel.CONDFALSE, displayLabel: 'Condfalse', position: 'right' },
    ],
  },
  defaults: {
    condition_type: 'custom',
  },
  customFields: conditionFields,
  primaryDisplayField: 'condition_type',
};

export default conditionConfig;