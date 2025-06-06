import React, { useEffect, useState, useRef } from 'react';
import { DiagramCanvas } from '@/components/diagram/canvas';
import { 
  useNodes, 
  usePersons,
  useSelectedPersonId,
  useSetSelectedPersonId 
} from '@/hooks/useStoreSelectors';

const ExecutionView = () => {
  const { persons } = usePersons();
  const { nodes } = useNodes();
  const selectedPersonId = useSelectedPersonId();
  const setSelectedPersonId = useSetSelectedPersonId();
  const [personPositions, setPersonPositions] = useState<Record<string, { x: number; y: number }>>({}); 
  const personRefs = useRef<Record<string, HTMLDivElement | null>>({});
  const canvasRef = useRef<HTMLDivElement>(null);
  
  // Find which nodes are assigned to which persons
  const personNodeMap = new Map<string, string[]>();
  nodes.forEach(node => {
    const personId = (node.data as any).personId;
    if (personId && typeof personId === 'string') {
      const nodeIds = personNodeMap.get(personId) || [];
      nodeIds.push(node.id);
      personNodeMap.set(personId, nodeIds);
    }
  });
  
  // Update person positions when persons change
  useEffect(() => {
    const updatePositions = () => {
      const newPositions: Record<string, { x: number; y: number }> = {};
      
      persons.forEach((person) => {
        const element = personRefs.current[person.id];
        if (element) {
          const rect = element.getBoundingClientRect();
          const canvasRect = canvasRef.current?.getBoundingClientRect();
          if (canvasRect) {
            newPositions[person.id] = {
              x: rect.left - canvasRect.left + rect.width / 2,
              y: rect.top - canvasRect.top
            };
          }
        }
      });
      
      setPersonPositions(newPositions);
    };
    
    // Update positions on mount and when persons change
    updatePositions();
    
    // Update on resize
    window.addEventListener('resize', updatePositions);
    return () => window.removeEventListener('resize', updatePositions);
  }, [persons]);

  return (
    <div className="h-full flex flex-col bg-gray-900">
      {/* Read-only Diagram Canvas */}
      <div className="flex-1 relative" ref={canvasRef}>
        <DiagramCanvas executionMode />
        
        {/* Connection lines from persons to nodes */}
        <svg className="absolute inset-0 pointer-events-none" style={{ zIndex: 10 }}>
          {persons.map(person => {
            const assignedNodes = personNodeMap.get(person.id) || [];
            const personPos = personPositions[person.id];
            
            if (!personPos || assignedNodes.length === 0) return null;
            
            return assignedNodes.map(nodeId => {
              const node = nodes.find(n => n.id === nodeId);
              if (!node || !node.position) return null;
              
              // Simple line from person to node center
              // Note: This is a simplified version. In production, you'd want to
              // calculate the actual node position in the viewport
              return (
                <line
                  key={`${person.id}-${nodeId}`}
                  x1={personPos.x}
                  y1={personPos.y}
                  x2={node.position.x + 100}
                  y2={node.position.y + 50}
                  stroke={selectedPersonId === person.id ? '#60a5fa' : '#9ca3af'}
                  strokeWidth="2"
                  strokeDasharray="5,5"
                  opacity={selectedPersonId === person.id ? 1 : 0.7}
                />
              );
            });
          })}
        </svg>
        
        {/* Persons displayed horizontally */}
        <div className="absolute bottom-0 left-0 right-0 bg-gray-800/90 backdrop-blur-sm border-t border-gray-600">
          <div className="flex items-center gap-4 p-4 overflow-x-auto">
            {persons.map(person => {
              const assignedNodes = personNodeMap.get(person.id) || [];
              return (
                <div 
                  key={person.id}
                  ref={(el) => {
                    if (el) {
                      personRefs.current[person.id] = el;
                    } else {
                      delete personRefs.current[person.id];
                    }
                  }}
                  className={`flex flex-col items-center min-w-[100px] cursor-pointer p-2 rounded transition-colors ${
                    selectedPersonId === person.id 
                      ? 'bg-blue-900/50 ring-2 ring-blue-500' 
                      : 'hover:bg-gray-800/50'
                  }`}
                  onClick={() => {
                    setSelectedPersonId(person.id);
                  }}
                >
                  <div className="w-12 h-12 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white font-bold mb-2">
                    {person.label.charAt(0).toUpperCase()}
                  </div>
                  <div className="text-white text-sm font-medium text-center">{person.label}</div>
                  <div className="text-gray-400 text-xs mt-1">
                    {assignedNodes.length} node{assignedNodes.length !== 1 ? 's' : ''}
                  </div>
                </div>
              );
            })}
            {persons.length === 0 && (
              <div className="text-gray-400 text-sm">No persons defined</div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ExecutionView;