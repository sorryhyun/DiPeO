// Auto-generated node configuration for api_job
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { apiJobFields } from '../fields/ApiJobFields';

export const apiJobConfig: UnifiedNodeConfig = {
  label: 'API Job',
  icon: '🌐',
  color: '#00BCD4',
  nodeType: 'api_job',
  category: 'integration',
  handles: {
    input: [
      { label: 'default', displayLabel: '', position: 'left' },
    ],
    output: [
      { label: 'default', displayLabel: 'Default', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: apiJobFields,
  primaryDisplayField: 'method',
};

export default apiJobConfig;