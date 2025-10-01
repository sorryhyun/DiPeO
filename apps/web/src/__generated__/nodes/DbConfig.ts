// Auto-generated node configuration for db
import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
import { NodeType, HandleLabel, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { dbFields } from '../fields/DbFields';

export const dbConfig: UnifiedNodeConfig = {
  label: 'Database',
  icon: '🗄️',
  color: '#795548',
  nodeType: NodeType.DB,
  category: 'integration',
  handles: {
    input: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'left' },
    ],
    output: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
    sub_type: 'fixed_prompt',
    operation: '',
    serialize_json: false,
    format: 'json',
  },
  customFields: dbFields,
  primaryDisplayField: 'operation',
};

export default dbConfig;
