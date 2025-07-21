import React from 'react';
import type { HookNodeData } from '@/core/types';
import ConfigurableNode from '../ConfigurableNode';

export function HookNode({ data }: { data: HookNodeData }) {
  return (
    <ConfigurableNode
      nodeType="hook"
      data={data}
      icon="🪝"
      color="#9333ea"
    />
  );
}