







// Auto-generated node configuration for sub_diagram
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { subDiagramFields } from '../fields/SubDiagramFields';

export const subDiagramConfig: UnifiedNodeConfig = {
  label: 'Sub-Diagram',
  icon: '📊',
  color: '#8B5CF6',
  nodeType: 'sub_diagram',
  category: 'control',
  handles: {
    input: [
      { label: 'default', displayLabel: '', position: 'left' },
    ],
    output: [
      { label: 'default', displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
    wait_for_completion: true,
    isolate_conversation: false,
    ignoreIfSub: false,
  },
  customFields: subDiagramFields,
  primaryDisplayField: 'diagram_path',
};

export default subDiagramConfig;