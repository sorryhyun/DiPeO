import React from 'react';
import { NodeProps } from '@xyflow/react';
import { GenericNode } from '../base/GenericNode';
import { Code, Zap, Link as LinkIcon } from 'lucide-react';
import { UNIFIED_NODE_CONFIGS, type JobBlockData } from '@/shared/types';

const JobNode: React.FC<NodeProps> = ({ id, data, selected }) => {
  const config = UNIFIED_NODE_CONFIGS.job;
  const jobData = data as JobBlockData;
  const subType = jobData.subType || 'code';
  const icon = subType === 'code' ? (
    <Code className="h-5 w-5 text-purple-600 flex-shrink-0" />
  ) : subType === 'api_tool' ? (
    <Zap className="h-5 w-5 text-blue-600 flex-shrink-0" />
  ) : (
    <LinkIcon className="h-5 w-5 text-green-600 flex-shrink-0" />
  );
  const subTypeLabel = subType === 'code' ? 'Code' : subType === 'api_tool' ? 'API Tool' : 'Diagram Link';
  const details = jobData.sourceDetails || '<configure job details>';

  return (
    <GenericNode id={id} data={data} selected={selected} nodeType={config.reactFlowType}>
      <div className="flex items-center space-x-2 mb-1">
        {icon}
        <strong className="text-base truncate">{jobData.label}</strong>
      </div>
      <div className="text-sm text-gray-400 mb-0.5">{subTypeLabel}</div>
      <p className="text-sm text-gray-500 truncate">{details}</p>
    </GenericNode>
  );
};

export default JobNode;