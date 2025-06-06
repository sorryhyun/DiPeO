import React from 'react';
import { Button } from '@/components/ui/buttons';
import { useDiagramRunner } from '@/hooks/useDiagramRunner';
import { useExecutionSelectors } from '@/hooks/useStoreSelectors';

const ExecutionControls = () => {
  const { 
    runStatus, 
    onRunDiagram, 
    stopExecution,
    pauseNode,
    resumeNode,
    skipNode
  } = useDiagramRunner();
  
  const { currentRunningNode } = useExecutionSelectors();

  return (
    <div className="flex items-center justify-center gap-4 p-4 bg-gray-800/50 backdrop-blur-sm border-b border-gray-700">
      {runStatus === 'running' ? (
        <>
          <Button 
            variant="outline" 
            className="bg-gradient-to-r from-red-500 to-red-600 text-white border-none hover:from-red-600 hover:to-red-700 shadow-md hover:shadow-lg transition-all"
            onClick={stopExecution}
          >
            ⏹️ Stop
          </Button>
          {currentRunningNode && (
            <>
              <Button
                variant="outline"
                className="bg-gradient-to-r from-yellow-500 to-amber-500 text-white border-none hover:from-yellow-600 hover:to-amber-600 shadow-md hover:shadow-lg transition-all"
                onClick={() => pauseNode(currentRunningNode)}
                title="Pause current node"
              >
                ⏸️ Pause
              </Button>
              <Button
                variant="outline"
                className="bg-gradient-to-r from-blue-500 to-cyan-500 text-white border-none hover:from-blue-600 hover:to-cyan-600 shadow-md hover:shadow-lg transition-all"
                onClick={() => resumeNode(currentRunningNode)}
                title="Resume current node"
              >
                ▶️ Resume
              </Button>
              <Button
                variant="outline"
                className="bg-gradient-to-r from-purple-500 to-pink-500 text-white border-none hover:from-purple-600 hover:to-pink-600 shadow-md hover:shadow-lg transition-all"
                onClick={() => skipNode(currentRunningNode)}
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
          onClick={onRunDiagram}
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

export default ExecutionControls;