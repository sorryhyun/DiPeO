import React from 'react';
import { NodeProps } from '@xyflow/react';
import { GenericNode } from '../base/GenericNode';
import { UNIFIED_NODE_TYPES, type DBBlockData } from '@/shared/types';

const DBNode: React.FC<NodeProps> = ({ id, data, selected }) => {
  const config = UNIFIED_NODE_TYPES.db;
  const dbData = data as DBBlockData;
  
  return (
    <GenericNode id={id} data={data} selected={selected} nodeType={config.reactFlowType} showFlipButton={false}>
      <div className="flex items-center space-x-2 mb-1">
        <span className="text-xl mr-2">{config.emoji}</span>
        <strong className="text-base truncate">{dbData.label || 'DB Source'}</strong>
      </div>
      <p className="text-sm text-gray-500 truncate">Type: {dbData.subType || 'N/A'}</p>
      <p className="text-sm text-gray-500 truncate">Source: {dbData.sourceDetails || 'N/A'}</p>
    </GenericNode>
  );
};

export default DBNode;