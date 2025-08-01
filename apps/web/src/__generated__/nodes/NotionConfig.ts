// Auto-generated node configuration for notion
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { notionFields } from '../fields/NotionFields';

export const notionConfig: UnifiedNodeConfig = {
  label: 'Notion',
  icon: '📝',
  color: '#ec4899',
  nodeType: 'notion',
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
  customFields: notionFields,
  primaryDisplayField: 'action',
};

export default notionConfig;