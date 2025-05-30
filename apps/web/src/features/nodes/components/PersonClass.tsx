// Component for Person nodes (LLM instances)
import React from 'react';
import { Position, NodeProps } from '@xyflow/react';
import { PersonDefinition } from '../../../shared/types';
import { User } from 'lucide-react';
import { FlowHandle, createHandleId } from '@/features/diagram/wrappers';

const PersonClass: React.FC<NodeProps> = ({ data, selected, id: nodeId }) => {
  const baseHandleStyle = 'w-3 h-3';
  return (
    <div className={`p-2 border-2 rounded-md shadow-md bg-white w-52 ${selected ? 'border-green-500 ring-2 ring-green-300' : 'border-gray-300'}`}>
      {/* Output handle for providing context or conversation stream */}
      <FlowHandle
        type="output"
        position={Position.Right}
        nodeId={nodeId}
        name="context"
        color="#16a34a"
      />
      {/* Memory tool handle for connecting memory storage */}
      <FlowHandle
        type="output"
        position={Position.Left}
        nodeId={nodeId}
        name="memory-tool"
        offset={25}
        color="#2563eb"
      />
      {/* API tool handle for connecting external API blocks */}
      <FlowHandle
        type="output"
        position={Position.Left}
        nodeId={nodeId}
        name="api-tool"
        offset={75}
        color="#2563eb"
      />
      <div className="flex items-center space-x-2 mb-1">
        <User className="h-5 w-5 text-green-600 flex-shrink-0" />
        <strong className="text-sm truncate" title={(data as unknown as PersonDefinition).label || 'Person'}>
          {(data as unknown as PersonDefinition).label || 'Person'}
        </strong>
      </div>
      <p className="text-xs text-gray-500 truncate">Service: {(data as unknown as PersonDefinition).service || 'Not set'}</p>
      <p className="text-xs text-gray-500 truncate">Model: {(data as unknown as PersonDefinition).modelName || 'Not set'}</p>
    </div>
  );
};
export default PersonClass;