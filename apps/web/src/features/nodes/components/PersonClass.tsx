// Component for Person nodes (LLM instances)
import React from 'react';
import { Position, NodeProps } from '@xyflow/react';
import { PersonDefinition } from '@/common/types';
import { User } from 'lucide-react';
import { FlowHandle } from './base/FlowHandle';
// import { createHandleId } from '@/common/utils/nodeHelpers';

const PersonClass: React.FC<NodeProps> = ({ data, selected, id: nodeId }) => {
  const [isDragging, setIsDragging] = React.useState(false);
  
  const handleDragStart = (e: React.DragEvent) => {
    e.dataTransfer.effectAllowed = 'copy';
    const personData = data as unknown as PersonDefinition;
    e.dataTransfer.setData('application/person', personData.id || nodeId);
    setIsDragging(true);
  };
  
  const handleDragEnd = () => {
    setIsDragging(false);
  };
  
  return (
    <div 
      className={`p-2 border-2 rounded-md shadow-md bg-white w-52 cursor-move transition-all ${
        selected ? 'border-green-500 ring-2 ring-green-300' : 'border-gray-300'
      } ${isDragging ? 'opacity-50 scale-95' : 'hover:shadow-lg'}`}
      draggable
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
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