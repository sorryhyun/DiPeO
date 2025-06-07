/**
 * useDiagramRunner - Compatibility wrapper for legacy code
 * 
 * This hook provides backward compatibility for code that used the old useDiagramRunner.
 * New code should use useExecutionV2 directly.
 */

import { useExecutionV2 } from './useExecutionV2';
import { useCallback } from 'react';

export function useDiagramRunner() {
  const execution = useExecutionV2({ autoConnect: true });
  
  // Map new API to old interface
  const runStatus = execution.isRunning ? 'running' : 
                   execution.executionState.error ? 'fail' :
                   execution.executionState.endTime ? 'success' : 'idle';
  
  const sendInteractiveResponse = useCallback((response: string) => {
    if (execution.interactivePrompt?.nodeId) {
      execution.respondToPrompt(execution.interactivePrompt.nodeId, response);
    }
  }, [execution]);
  
  const cancelInteractivePrompt = useCallback(() => {
    if (execution.interactivePrompt?.nodeId) {
      execution.respondToPrompt(execution.interactivePrompt.nodeId, '');
    }
  }, [execution]);
  
  return {
    runStatus,
    runError: execution.executionState.error,
    retryCount: 0, // Not tracked in new version
    onRunDiagram: execution.execute,
    stopExecution: execution.abort,
    pauseNode: execution.pauseNode,
    resumeNode: execution.resumeNode,
    skipNode: execution.skipNode,
    interactivePrompt: execution.interactivePrompt,
    sendInteractiveResponse,
    cancelInteractivePrompt,
  };
}