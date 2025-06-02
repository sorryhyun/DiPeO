import React from 'react';
import { NodeProps } from '@xyflow/react';
import { GenericNode } from '../base/GenericNode';
import { Save } from 'lucide-react';
import { UNIFIED_NODE_CONFIGS, type EndpointBlockData } from '@/shared/types';

const EndpointNode: React.FC<NodeProps> = ({ id, data, selected }) => {
  const config = UNIFIED_NODE_CONFIGS.endpoint;
  const endpointData = data as EndpointBlockData;
  
  if (!config) {
    return null;
  }
  
  return (
    <GenericNode id={id} data={data} selected={selected} nodeType={config.reactFlowType}>
      <span className="text-2xl mb-0.5">{config.emoji}</span>
      <strong className="text-sm truncate">{endpointData.label || 'End'}</strong>
      {endpointData.saveToFile && (
        <div className="flex items-center gap-1 mt-1">
          <Save className="h-3 w-3 text-gray-600" />
          <span className="text-xs text-gray-600">Save</span>
        </div>
      )}
    </GenericNode>
  );
};

export default EndpointNode;