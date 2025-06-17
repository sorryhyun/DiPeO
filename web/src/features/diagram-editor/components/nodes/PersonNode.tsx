// Component for Person nodes (LLM instances)
import React, { useCallback } from 'react';
import { Position, NodeProps } from '@xyflow/react';
import { DomainPerson } from '@/core/types';
import { nodeId as createNodeId } from '@/core/types';
import { User } from 'lucide-react';
import { FlowHandle } from '../controls/FlowHandle';

const PersonClass: React.FC<NodeProps> = React.memo(({ data, selected, id }) => {
  const [isDragging, setIsDragging] = React.useState(false);
  
  // Cast data once to avoid repeated casting
  const personData = data as unknown as DomainPerson;
  const nodeIdTyped = createNodeId(id);
  
  const handleDragStart = useCallback((e: React.DragEvent) => {
    e.dataTransfer.effectAllowed = 'copy';
    e.dataTransfer.setData('application/person', personData.id || id);
    setIsDragging(true);
  }, [personData.id, id]);
  
  const handleDragEnd = useCallback(() => {
    setIsDragging(false);
  }, []);
  
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
        nodeId={nodeIdTyped}
        label="context"
        color="#16a34a"
      />
      {/* Memory tool handle for connecting memory storage */}
      <FlowHandle
        type="output"
        position={Position.Left}
        nodeId={nodeIdTyped}
        label="memory-tool"
        offset={25}
        color="#2563eb"
      />
      {/* API tool handle for connecting external API blocks */}
      <FlowHandle
        type="output"
        position={Position.Left}
        nodeId={nodeIdTyped}
        label="api-tool"
        offset={75}
        color="#2563eb"
      />
      <div className="flex items-center space-x-2 mb-1">
        <User className="h-5 w-5 text-green-600 flex-shrink-0" />
        <strong className="text-sm truncate" title={personData.label || 'Person'}>
          {personData.label || 'Person'}
        </strong>
      </div>
      <p className="text-xs text-gray-500 truncate">Model: {personData.model || 'Not set'}</p>
    </div>
  );
}, (prevProps, nextProps) => {
  // Custom comparison to prevent unnecessary re-renders
  const prevData = prevProps.data as unknown as DomainPerson;
  const nextData = nextProps.data as unknown as DomainPerson;
  
  return (
    prevProps.id === nextProps.id &&
    prevProps.selected === nextProps.selected &&
    prevData.label === nextData.label &&
    prevData.model === nextData.model
  );
});

PersonClass.displayName = 'PersonNode';

export default PersonClass;