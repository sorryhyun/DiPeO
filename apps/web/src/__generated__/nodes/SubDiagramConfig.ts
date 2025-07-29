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
      { id: 'data', label: '', position: 'left' },
    ],
    output: [
      { id: 'result', label: '', position: 'right' },
    ],
  },
  defaults: {
  },
  customFields: subDiagramFields,
};

export default subDiagramConfig;