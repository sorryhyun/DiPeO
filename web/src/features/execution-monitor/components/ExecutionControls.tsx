import React from 'react';
import { Button } from '@/shared/components/ui/buttons';
import { useExecution } from '../hooks';
import { useDiagramData } from '@/shared/hooks/selectors';
import { useUnifiedStore } from '@/core/store/unifiedStore';
import { nodeId } from '@/core/types';

const ExecutionControls = () => {
  const execution = useExecution({ showToasts: false });
  const { nodes, arrows } = useDiagramData();
  const { persons, handles, apiKeys } = useUnifiedStore(state => ({
    persons: state.persons,
    handles: state.handles,
    apiKeys: state.apiKeys
  }));
  
  // Map execution state to old runStatus format
  const runStatus = execution.isRunning ? 'running' : 
                   execution.execution.error ? 'fail' :
                   execution.execution.endTime ? 'success' : 'idle';
  
  // Get current running node from execution state
  const currentRunningNode = execution.execution.currentNode;

  return (
    <div className="flex items-center justify-center gap-4 p-4 bg-gray-800/50 backdrop-blur-sm border-b border-gray-700">
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
      ) : (
        <Button 
          variant="outline" 
          className="bg-gradient-to-r from-green-500 to-emerald-500 text-white border-none hover:from-green-600 hover:to-emerald-600 shadow-md hover:shadow-lg transition-all"
          onClick={() => {
            // Convert Maps to arrays for DomainDiagram format
            const diagram = {
              nodes: Array.from(nodes.values()),
              arrows: Array.from(arrows.values()),
              persons: Array.from(persons.values()),
              handles: Array.from(handles.values()),
              apiKeys: Array.from(apiKeys.values()),
              nodeCount: nodes.size,
              arrowCount: arrows.size,
              personCount: persons.size
            };
            execution.execute(diagram);
          }}
        >
          ▶️ Run Diagram
        </Button>
      )}
      
      <div className="whitespace-nowrap text-base font-medium ml-4">
        {runStatus === 'running' && <span className="text-blue-400 animate-pulse">⚡ Running...</span>}
        {runStatus === 'success' && <span className="text-green-400">✅ Success</span>}
        {runStatus === 'fail' && <span className="text-red-400">❌ Fail</span>}
      </div>
    </div>
  );
};

export { ExecutionControls };