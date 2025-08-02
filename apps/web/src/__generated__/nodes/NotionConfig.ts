







// Auto-generated node configuration for notion
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/domain-models';
import { notionFields } from '../fields/NotionFields';

export const notionConfig: UnifiedNodeConfig = {
  label: 'Notion',
  icon: '📝',
  color: '#ec4899',
  nodeType: NodeType.NOTION,
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
  },
  customFields: notionFields,
  primaryDisplayField: 'action',
};

export default notionConfig;