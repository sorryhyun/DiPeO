// apps/web/src/components/diagram/MemoryLayer.tsx
import React from 'react';
import { usePersonStore, useNodeArrowStore } from '@/global/stores';
import { MessageSquare, Database } from 'lucide-react';

const MemoryLayer: React.FC = () => {
  const { persons } = usePersonStore();
  const { nodes } = useNodeArrowStore();
  // Execution store available if needed
  // const { runContext } = useExecutionStore();

  // Get person job nodes to position memory beneath them
  const personJobNodes = nodes.filter(n => n.type === 'person_job');

  return (
    <div className="absolute inset-0 pointer-events-none">
      {/* Memory blocks positioned under person job nodes */}
      {personJobNodes.map(node => {
        const person = persons.find(p => p.id === node.data.personId);
        if (!person) return null;

        return (
          <div
            key={`memory-${node.id}`}
            className="absolute transform translate-y-20"
            style={{
              left: node.position.x,
              top: node.position.y,
              width: 200,
            }}
          >
            <div className="bg-purple-900/80 text-white rounded-lg p-3 shadow-xl backdrop-blur-sm">
              <div className="flex items-center space-x-2 mb-2">
                <Database className="h-4 w-4" />
                <span className="text-sm font-medium">Memory</span>
              </div>
              <div className="text-xs opacity-80">
                {person.label || 'Unknown Person'}
              </div>
              <div className="mt-2 text-xs">
                <div className="flex items-center space-x-1">
                  <MessageSquare className="h-3 w-3" />
                  <span>12 messages</span>
                </div>
              </div>
            </div>

            {/* Connection line */}
            <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-20 w-0.5 h-20 bg-purple-400/50"></div>
          </div>
        );
      })}

      {/* Underground plane indicator */}
      <div className="absolute inset-x-0 bottom-0 h-32 bg-gradient-to-t from-purple-900/20 to-transparent"></div>
    </div>
  );
};

export default MemoryLayer;