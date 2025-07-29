// Auto-generated node configuration for endpoint
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { endpointFields } from '../fields/EndpointFields';

export const endpointConfig: UnifiedNodeConfig = {
  label: 'End Node',
  icon: '🏁',
  color: '#F44336',
  nodeType: 'endpoint',
  category: 'control',
  handles: {
    input: [
      { label: 'default', displayLabel: '', position: 'left' },
    ],
  },
  defaults: {
  },
  customFields: endpointFields,
};

export default endpointConfig;