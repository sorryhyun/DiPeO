import { Position } from '@xyflow/react';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import type { NodeData } from '@/core/types';
import { Fields } from './Fields';

export const NodeConfig: UnifiedNodeConfig<NodeData> = {
  nodeType: '' as const,
  label: '',
  icon: '',
  color: '',
  
  handles: {
    input: [
    ],
    output: [
    ]
  },
  
  defaults: {
    label: '',
  },
  
  customFields: Fields
};