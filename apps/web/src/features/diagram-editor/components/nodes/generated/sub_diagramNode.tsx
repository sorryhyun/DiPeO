import React from 'react';
import type { NodeProps } from '@xyflow/react';
import ConfigurableNode from '../ConfigurableNode';

export function SubDiagramNode(props: NodeProps) {
  return <ConfigurableNode {...props} />;
}