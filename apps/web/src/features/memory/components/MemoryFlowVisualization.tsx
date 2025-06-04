import React from 'react';
import { usePersonStore, useNodeArrowStore, useExecutionStore } from '@/state/stores';
import { Users, MessageSquare, Database, Zap } from 'lucide-react';

const MemoryFlowVisualization: React.FC = () => {
  const { persons } = usePersonStore();
  const { nodes, arrows } = useNodeArrowStore();
  const { runContext } = useExecutionStore();

  // Get person job nodes to position memory beneath them
  const personJobNodes = nodes.filter(n => n.type === 'person_job');

  // Create memory connections between persons based on arrows
  const createMemoryConnections = () => {
    const connections: Array<{
      from: { x: number; y: number; personId: string };
      to: { x: number; y: number; personId: string };
      label: string;
    }> = [];

    arrows.forEach(arrow => {
      const sourceNode = nodes.find(n => n.id === arrow.source);
      const targetNode = nodes.find(n => n.id === arrow.target);
      
      if (sourceNode?.type === 'person_job' && targetNode?.type === 'person_job') {
        const sourcePerson = persons.find(p => p.id === sourceNode.data.personId);
        const targetPerson = persons.find(p => p.id === targetNode.data.personId);
        
        if (sourcePerson && targetPerson) {
          connections.push({
            from: { 
              x: sourceNode.position.x + 100, 
              y: sourceNode.position.y + 50,
              personId: sourcePerson.id 
            },
            to: { 
              x: targetNode.position.x + 100, 
              y: targetNode.position.y + 50,
              personId: targetPerson.id 
            },
            label: String(arrow.label || 'data_flow')
          });
        }
      }
    });

    return connections;
  };

  const memoryConnections = createMemoryConnections();

  return (
    <div className="absolute inset-0 bg-gradient-to-b from-slate-800 to-slate-900 overflow-hidden">
      {/* Memory Blocks positioned under person job nodes */}
      {personJobNodes.map(node => {
        const person = persons.find(p => p.id === node.data.personId);
        if (!person) return null;

        // Get execution context for this person
        const personsData = runContext?.persons as Record<string, { messages?: unknown[] }> | undefined;
        const personMessages = personsData?.[person.id]?.messages || [];
        const messageCount = Array.isArray(personMessages) ? personMessages.length : 0;

        return (
          <div
            key={`memory-${node.id}`}
            className="absolute transform transition-all duration-500 hover:scale-105"
            style={{
              left: `${node.position.x}px`,
              top: `${node.position.y + 100}px`,
              width: '220px',
            }}
          >
            {/* Memory Block */}
            <div className="bg-gradient-to-br from-purple-900/90 to-indigo-900/90 text-white rounded-xl p-4 shadow-2xl backdrop-blur-sm border border-purple-500/30">
              <div className="flex items-center space-x-2 mb-3">
                <Database className="h-5 w-5 text-purple-300" />
                <span className="text-sm font-semibold">Memory Core</span>
              </div>
              
              <div className="text-xs text-purple-200 mb-3">
                {person.label || 'Unknown Person'}
              </div>
              
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1">
                    <MessageSquare className="h-3 w-3 text-blue-300" />
                    <span className="text-xs text-blue-200">Messages</span>
                  </div>
                  <span className="text-xs font-mono text-white">{messageCount}</span>
                </div>
                
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-1">
                    <Users className="h-3 w-3 text-green-300" />
                    <span className="text-xs text-green-200">Connections</span>
                  </div>
                  <span className="text-xs font-mono text-white">
                    {memoryConnections.filter(c => c.from.personId === person.id || c.to.personId === person.id).length}
                  </span>
                </div>
                
                <div className="h-1 bg-purple-800 rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-gradient-to-r from-purple-400 to-blue-400 transition-all duration-1000"
                    style={{ width: `${Math.min(100, (messageCount / 10) * 100)}%` }}
                  />
                </div>
              </div>
              
              {/* Activity indicator */}
              {(() => {
                const executionCounts = runContext?.nodeExecutionCounts as Record<string, number> | undefined;
                const count = executionCounts?.[node.id] || 0;
                return count > 0 ? (
                  <div className="mt-2 flex items-center space-x-1">
                    <Zap className="h-3 w-3 text-yellow-400 animate-pulse" />
                    <span className="text-xs text-yellow-300">Active</span>
                  </div>
                ) : null;
              })()}
            </div>

            {/* Connection line to diagram above */}
            <div className="absolute top-0 left-1/2 transform -translate-x-1/2 -translate-y-24 w-0.5 h-24 bg-gradient-to-t from-purple-400 to-transparent"></div>
          </div>
        );
      })}

      {/* Memory Flow Connections */}
      <svg className="absolute inset-0 pointer-events-none" style={{ zIndex: 1 }}>
        {memoryConnections.map((connection, index) => {
          const midX = (connection.from.x + connection.to.x) / 2;
          const midY = (connection.from.y + connection.to.y) / 2 + 150;
          
          return (
            <g key={`connection-${index}`}>
              {/* Curved path for memory flow */}
              <path
                d={`M ${connection.from.x + 110} ${connection.from.y + 150} 
                   Q ${midX} ${midY} 
                   ${connection.to.x + 110} ${connection.to.y + 150}`}
                stroke="url(#memoryGradient)"
                strokeWidth="2"
                fill="none"
                strokeDasharray="8,4"
                className="animate-pulse"
              />
              
              {/* Arrow marker */}
              <circle
                cx={connection.to.x + 110}
                cy={connection.to.y + 150}
                r="3"
                fill="#8b5cf6"
                className="animate-pulse"
              />
              
              {/* Data flow label */}
              <text
                x={midX}
                y={midY - 10}
                fill="#a855f7"
                fontSize="10"
                textAnchor="middle"
                className="font-mono"
              >
                {connection.label}
              </text>
            </g>
          );
        })}
        
        {/* Gradient definition */}
        <defs>
          <linearGradient id="memoryGradient" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.8" />
            <stop offset="50%" stopColor="#3b82f6" stopOpacity="1" />
            <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0.8" />
          </linearGradient>
        </defs>
      </svg>

      {/* Underground memory grid */}
      <div className="absolute inset-0 opacity-20">
        <div className="grid grid-cols-12 grid-rows-8 h-full w-full">
          {Array.from({ length: 96 }).map((_, i) => (
            <div
              key={i}
              className="border border-purple-500/20 bg-purple-900/10"
              style={{
                animationDelay: `${i * 50}ms`,
                animation: 'pulse 3s infinite'
              } as React.CSSProperties}
            />
          ))}
        </div>
      </div>
      
      {/* Memory layer indicator */}
      <div className="absolute bottom-4 right-4 bg-purple-900/90 text-purple-200 px-3 py-2 rounded-lg backdrop-blur-sm border border-purple-500/30">
        <div className="flex items-center space-x-2">
          <Database className="h-4 w-4" />
          <span className="text-sm font-medium">Memory Layer Active</span>
        </div>
      </div>
    </div>
  );
};

export default MemoryFlowVisualization;