







// Auto-generated node configuration for sub_diagram
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import { NodeType, HandleLabel, MemoryProfile, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/domain-models';
import { subDiagramFields } from '../fields/SubDiagramFields';

export const subDiagramConfig: UnifiedNodeConfig = {
  label: 'Sub-Diagram',
  icon: '📊',
  color: '#8B5CF6',
  nodeType: NodeType.SUB_DIAGRAM,
  category: 'control',
  handles: {
    input: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'left' },
    ],
    output: [
      { label: HandleLabel.DEFAULT, displayLabel: '', position: 'right' },
    ],
  },
  defaults: {
    wait_for_completion: true,
    isolate_conversation: false,
    ignoreIfSub: false,
    batch: false,
    batch_parallel: false,
  },
  customFields: subDiagramFields,
  primaryDisplayField: 'diagram_name',
};

export default subDiagramConfig;