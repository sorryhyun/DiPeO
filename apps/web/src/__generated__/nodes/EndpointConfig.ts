// Auto-generated node configuration for endpoint
import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
import { NodeType, HandleLabel, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { endpointFields } from '../fields/EndpointFields';

export const endpointConfig: UnifiedNodeConfig = {
  label: 'End Node',
  icon: '🏁',
  color: '#F44336',
  nodeType: NodeType.ENDPOINT,
  category: 'control',
  handles: {
    input: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'left' },
    ],
  },
  defaults: {
  },
  customFields: endpointFields,
  primaryDisplayField: 'save_to_file',
};

export default endpointConfig;
