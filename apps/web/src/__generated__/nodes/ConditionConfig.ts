// Auto-generated node configuration for condition
import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
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
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'right' },
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: conditionFields,
  primaryDisplayField: 'condition_type',
};

export default conditionConfig;