import { Position } from '@xyflow/react';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import type { HookNodeData } from '@/core/types';
import { hookFields } from './hookFields';

export const HookNodeConfig: UnifiedNodeConfig<HookNodeData> = {
  nodeType: 'hook' as const,
  label: 'Hook',
  icon: '🪝',
  color: '#9333ea',
  category: 'control',
  description: 'Executes hooks at specific points in the diagram execution',
  
  handles: {
    sources: [
      { id: 'success', position: Position.Right },
      { id: 'error', position: Position.Right },
    ],
    targets: [
      { id: 'trigger', position: Position.Left },
    ]
  },
  
  defaults: {
    label: 'Hook',
    hook_type: 'shell',
    timeout: 60,
  },
  
  customFields: hookFields
};