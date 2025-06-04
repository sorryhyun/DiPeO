// Universal Node Component
import React from 'react';
import { NodeProps } from '@xyflow/react';
import ConfigurableNode from './ConfigurableNode';

// Universal Node Component - now just uses ConfigurableNode directly
const UniversalNode: React.FC<NodeProps> = (props) => {
  return <ConfigurableNode {...props} />;
};

export default UniversalNode;