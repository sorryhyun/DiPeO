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
      { id: 'data', label: '', position: 'left' },
    ],
    output: [
      { id: 'result', label: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: notionFields,
};

export default notionConfig;