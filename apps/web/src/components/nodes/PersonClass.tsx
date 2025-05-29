// Component for Person nodes (LLM instances)
import React from 'react';
import { Handle, Position, NodeProps } from '@xyflow/react';
import { PersonDefinition } from '@repo/core-model';
import { User } from 'lucide-react';
import { createHandleId } from '@repo/diagram-ui';

const PersonClass: React.FC<NodeProps> = ({ data, selected, id: nodeId }) => {
  const baseHandleStyle = 'w-3 h-3';
  return (
    <div className={`p-2 border-2 rounded-md shadow-md bg-white w-52 ${selected ? 'border-green-500 ring-2 ring-green-300' : 'border-gray-300'}`}>
      {/* Output handle for providing context or conversation stream */}
      <Handle
        type="source"
        position={Position.Right}
        id={createHandleId(nodeId, 'output', 'context')}
        style={{ top: '50%' }}
        className={`${baseHandleStyle} !bg-green-500`}
      />
      {/* Memory tool handle for connecting memory storage */}
      <Handle
        type="source"
        position={Position.Left}
        id={createHandleId(nodeId, 'output', 'memory-tool')}
        style={{ top: '25%' }}
        className={`${baseHandleStyle} !bg-yellow-500`}
      />
      {/* API tool handle for connecting external API blocks */}
      <Handle
        type="source"
        position={Position.Left}
        id={createHandleId(nodeId, 'output', 'api-tool')}
        style={{ top: '75%' }}
        className={`${baseHandleStyle} !bg-blue-500`}
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