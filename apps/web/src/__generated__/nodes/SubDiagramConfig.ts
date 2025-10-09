// Auto-generated node configuration for sub_diagram
import type { UnifiedNodeConfig } from '@/infrastructure/config/unifiedConfig';
import { NodeType, HandleLabel, ToolSelection, HookType, HttpMethod, SupportedLanguage, HookTriggerMode } from '@dipeo/models';
import { subDiagramFields } from '../fields/SubDiagramFields';

export const subDiagramConfig: UnifiedNodeConfig = {
  label: 'Sub-Diagram',
  icon: '📊',
  color: '#8B5CF6',
  nodeType: NodeType.SUB_DIAGRAM,
  category: 'compute',
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
    ignore_if_sub: false,
    batch: false,
    batch_input_key: 'items',
    batch_parallel: true,
  },
  customFields: subDiagramFields,
  primaryDisplayField: 'diagram_name',
};

export default subDiagramConfig;
