import React from 'react';
import { Button } from '@/ui/components/common/forms/buttons';
import { useExecution } from '@/domain/execution/hooks';
import { useMonitorMode } from '@/domain/execution/hooks';
import { useNodesData, useArrowsData, usePersonsData, useDiagramData as useStoreDiagramData } from '@/infrastructure/store/hooks';
import { nodeId, diagramId, DomainDiagram } from '@/infrastructure/types';
import { toast } from 'sonner';

const ExecutionControls = () => {
  const { isMonitorMode, diagramName } = useMonitorMode();
  const execution = useExecution({ showToasts: false });
  const nodes = useNodesData();
  const arrows = useArrowsData();
  const persons = usePersonsData();
  const { handles } = useStoreDiagramData();
  
  // Map execution state to old runStatus format
  const runStatus = execution.isRunning ? 'running' : 
                   execution.execution.error ? 'fail' :
                   execution.execution.endTime ? 'success' : 'idle';
  
  // Get current running node from execution state
  const currentRunningNode = null; // TODO: Get from nodeStates or running nodes

  return (
    <div className="flex items-center justify-center gap-4 p-4 bg-gray-800/50 backdrop-blur-sm border-b border-gray-700">
      {/* Monitor Mode Indicator */}
      {isMonitorMode && (
        <div className="flex items-center gap-2 px-3 py-1.5 bg-blue-500/20 text-blue-300 rounded-md border border-blue-500/30">
          <span className="animate-pulse">📡</span>
          <span className="text-sm font-medium">
            Monitor Mode {diagramName ? `- ${diagramName}` : ''}
          </span>
        </div>
      )}
      
      {runStatus === 'running' ? (
        <>
          <Button 
            variant="outline" 
            className="bg-gradient-to-r from-red-500 to-red-600 text-white border-none hover:from-red-600 hover:to-red-700 shadow-md hover:shadow-lg transition-all"
            onClick={execution.abort}
          >
            ⏹️ Stop
          </Button>
          {currentRunningNode && (
            <>
              <Button
                variant="outline"
                className="bg-gradient-to-r from-yellow-500 to-amber-500 text-white border-none hover:from-yellow-600 hover:to-amber-600 shadow-md hover:shadow-lg transition-all"
                onClick={() => execution.pauseNode(nodeId(currentRunningNode))}
                title="Pause current node"
              >
                ⏸️ Pause
              </Button>
              <Button
                variant="outline"
                className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white border-none hover:from-blue-600 hover:to-cyan-600 shadow-md hover:shadow-lg transition-all"
                onClick={() => execution.resumeNode(nodeId(currentRunningNode))}
                title="Resume current node"
              >
                ▶️ Resume
              </Button>
              <Button
                variant="outline"
                className="bg-gradient-to-r from-purple-500 to-pink-500 text-white border-none hover:from-purple-600 hover:to-pink-600 shadow-md hover:shadow-lg transition-all"
                onClick={() => execution.skipNode(nodeId(currentRunningNode))}
                title="Skip current node"
              >
                ⏭️ Skip
              </Button>
            </>
          )}
        </>
      ) : !isMonitorMode ? (
        <Button 
          variant="outline" 
          className="bg-gradient-to-r from-green-500 to-emerald-500 text-white border-none hover:from-green-600 hover:to-emerald-600 shadow-md hover:shadow-lg transition-all"
          onClick={async () => {
            try {
              // Create a DomainDiagram for in-memory execution
              const diagramForExecution: DomainDiagram = {
                metadata: {
                  id: diagramId(`temp-execution-${Date.now()}`),
                  created: new Date().toISOString(),
                  modified: new Date().toISOString(),
                  version: '1.0',
                  name: 'Execution Diagram',
                  description: null,
                  author: null,
                  tags: []
                },
                nodes,
                arrows,
                persons,
                handles
              };
              
              // Execute using the diagram data directly (no file save)
              await execution.execute(diagramForExecution);
            } catch (error) {
              console.error('Failed to execute diagram:', error);
              toast.error('Failed to execute diagram');
            }
          }}
        >
          ▶️ Run Diagram
        </Button>
      ) : null}
      
      <div className="whitespace-nowrap text-base font-medium ml-4">
        {runStatus === 'running' && <span className="text-blue-400 animate-pulse">⚡ Running...</span>}
        {runStatus === 'success' && <span className="text-green-400">✅ Success</span>}
        {runStatus === 'fail' && <span className="text-red-400">❌ Fail</span>}
      </div>
    </div>
  );
};

export { ExecutionControls };