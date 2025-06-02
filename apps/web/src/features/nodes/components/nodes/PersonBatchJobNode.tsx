import React from 'react';
import { NodeProps } from '@xyflow/react';
import { PersonBatchJobBlockData } from '@/shared/types';
import { GenericNode } from '../base/GenericNode';

const PersonBatchJobNode: React.FC<NodeProps> = ({ id, data, selected }) => {
  const batchJobData = data as PersonBatchJobBlockData;
  
  return (
    <GenericNode
      id={id}
      data={data}
      selected={selected}
      nodeType="person_batch_job"
    >
      <div className="text-center">
        <div className="text-sm font-medium">{batchJobData.label || 'Person Batch Job'}</div>
        {batchJobData.personId && (
          <div className="text-xs text-gray-500 mt-1">
            Batch Size: {batchJobData.batchSize || 10}
          </div>
        )}
      </div>
    </GenericNode>
  );
};

export default PersonBatchJobNode;