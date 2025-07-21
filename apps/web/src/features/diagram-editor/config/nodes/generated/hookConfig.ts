import { Position } from '@xyflow/react';
import type { UnifiedNodeConfig } from '@/core/config/unifiedConfig';
import type { HookNodeData } from '@/core/types';
import { hookFields } from './hookFields';

export const HookNodeConfig: UnifiedNodeConfig<HookNodeData> = {
  nodeType: 'hook' as const,
  label: 'Hook',
  icon: '🪝',
  color: '#9333ea',
  
  handles: {
    input: [
      { id: 'trigger', position: Position.Left },
    ],
    output: [
      { id: 'success', position: Position.Right },
      { id: 'error', position: Position.Right },
    ]
  },
  
  defaults: {
    label: 'Hook',
    hook_type: 'shell',
    timeout: 60,
  },
  
  customFields: hookFields
};