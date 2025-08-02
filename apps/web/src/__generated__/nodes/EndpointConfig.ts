







// Auto-generated node configuration for endpoint
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/domain-models';
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
  primaryDisplayField: 'path',
};

export default endpointConfig;