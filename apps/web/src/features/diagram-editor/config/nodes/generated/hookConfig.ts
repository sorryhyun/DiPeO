import { Position } from '@xyflow/react';
import { HandleLabel } from '@dipeo/domain-models';
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
      { id: HandleLabel.DEFAULT, position: Position.Left },
    ],
    output: [
      { id: HandleLabel.SUCCESS, position: Position.Right },
      { id: HandleLabel.ERROR, position: Position.Right },
    ]
  },
  
  defaults: {
    label: 'Hook',
    hook_type: 'shell',
    timeout: 60,
  },
  
  customFields: hookFields
};