







// Generated field configuration for integrated_api
import type { UnifiedFieldDefinition } from '@/core/config/unifiedConfig';

export const integratedApiFields: UnifiedFieldDefinition[] = [
  {
    name: 'provider',
    type: 'select',
    label: 'Provider',
    required: true,
    description: 'API provider to connect to',
    options: [
      { value: 'notion', label: 'Notion' },
      { value: 'slack', label: 'Slack' },
      { value: 'github', label: 'GitHub' },
      { value: 'jira', label: 'Jira' },
      { value: 'google_search', label: 'Google Search' },
    ],
    validate: (value: unknown) => {
      return { isValid: true };
    },
  },
  {
    name: 'operation',
    type: 'select',
    label: 'Operation',
    required: true,
    placeholder: 'Select an operation',
    description: 'Operation to perform (provider-specific)',
  },
  {
    name: 'resource_id',
    type: 'text',
    label: 'Resource Id',
    required: false,
    placeholder: 'Resource ID (if applicable)',
    description: 'Resource identifier (e.g., page ID, channel ID)',
  },
  {
    name: 'config',
    type: 'code',
    label: 'Config',
    required: false,
    placeholder: '{ /* provider-specific config */ }',
    description: 'Provider-specific configuration',
  },
  {
    name: 'timeout',
    type: 'number',
    label: 'Timeout',
    required: false,
    placeholder: '30',
    description: 'Request timeout in seconds',
    validate: (value: unknown) => {
      if (typeof value === 'number' && value < 1) {
        return { isValid: false, error: 'Value must be at least 1' };
      }
      if (typeof value === 'number' && value > 300) {
        return { isValid: false, error: 'Value must be at most 300' };
      }
      return { isValid: true };
    },
  },
  {
    name: 'max_retries',
    type: 'number',
    label: 'Max Retries',
    required: false,
    placeholder: '3',
    description: 'Maximum retry attempts',
    validate: (value: unknown) => {
      if (typeof value === 'number' && value < 0) {
        return { isValid: false, error: 'Value must be at least 0' };
      }
      if (typeof value === 'number' && value > 10) {
        return { isValid: false, error: 'Value must be at most 10' };
      }
      return { isValid: true };
    },
  },
];