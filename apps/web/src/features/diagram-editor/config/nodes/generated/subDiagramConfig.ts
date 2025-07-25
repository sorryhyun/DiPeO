import { Position } from '@xyflow/react';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import type { SubDiagramNodeData } from '@/core/types';
import { subDiagramFields } from './subDiagramFields';

export const SubDiagramNodeConfig: UnifiedNodeConfig<SubDiagramNodeData> = {
  nodeType: 'sub_diagram' as const,
  label: 'Sub-Diagram',
  icon: '📊',
  color: '#8B5CF6',
  
  handles: {
    input: [
      { id: 'default', position: Position.Left },
    ],
    output: [
      { id: 'default', position: Position.Right },
      { id: 'results', position: Position.Right },
      { id: 'error', position: Position.Right },
    ]
  },
  
  defaults: {
    label: 'Sub-Diagram',
    wait_for_completion: true,
  },
  
  customFields: subDiagramFields
};